"""绘图数据边界测试; 仅构造测试指标, 不生成性能图或正式科学结果."""

import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_plot_data import BOOTSTRAP_REPLICATES, BOOTSTRAP_SEED, METHODS, METRICS, prepare_plot_data


class PlotDataTest(unittest.TestCase):
    def setUp(self):
        workspace = Path(__file__).resolve().parents[5]
        temporary_root = workspace / "temp" / "ligandseek1_plot_data_gate"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=temporary_root)
        self.root = Path(self.temporary.name)
        self.full_ids = ["test_a", "test_b", "test_c"]
        self.small_ids = ["test_c", "test_a"]
        self.fields = ("semantic_macro_f1", "one_to_one_macro_prauc_0p3", "one_to_one_macro_prauc_0p5", "one_to_one_macro_precision_0p3", "one_to_one_macro_recall_0p3")
        self.small_fields = ("semantic_dice", "one_to_one_prauc_0p3", "one_to_one_prauc_0p5", "one_to_one_precision_0p3", "one_to_one_recall_0p3")
        base = {"test_a": 0.0, "test_b": 0.5, "test_c": 1.0}
        self.l2 = {
            "resolution": {"test_a": 2.0, "test_b": 3.0, "test_c": 4.0},
            "models": {
                receptor: {
                    "full_rows": [{"pdb_id": pdb, **dict.fromkeys(self.fields, base[pdb])} for pdb in self.full_ids],
                    "small_rows": [{"pdb_id": pdb, **dict.fromkeys(self.small_fields, base[pdb])} for pdb in self.small_ids],
                } for receptor in ("GT", "Cryo")
            },
        }
        self.l2_path = self.root / "ligandseek2.json"
        self.l2_path.write_text(json.dumps(self.l2), encoding="utf-8")
        self.manifest = self.root / "inputs.json"
        self.manifest.write_text(json.dumps({"test_0_pdb_ids": self.full_ids, "small_pdb_ids": self.small_ids}), encoding="utf-8")
        self.l1_root = self.root / "ligandseek1"
        for mode in ("deposited", "inferred"):
            values = base if mode == "deposited" else {"test_a": 0.0, "test_b": 0.25, "test_c": 1.0}
            for folder, ids in (("evaluation", self.full_ids), ("small_molecule_only", self.small_ids)):
                destination = self.l1_root / mode / "held_out_test_0" / folder / "official_pv.jsonl"
                destination.parent.mkdir(parents=True)
                destination.write_text("\n".join(json.dumps({"pdb_id": pdb, **dict.fromkeys(self.fields, values[pdb])}) for pdb in ids), encoding="utf-8")
        self.output = self.root / "plot"

    def tearDown(self):
        self.temporary.cleanup()

    def test_frozen_values_members_pairing_and_csv(self):
        prepare_plot_data(self.l2_path, self.l1_root, self.manifest, self.output)
        result = json.loads((self.output / "plot_data.json").read_text(encoding="utf-8"))
        full = result["cohorts"]["full"]
        self.assertEqual(full["ids"], self.full_ids)
        self.assertEqual(full["models"]["L1_CA2"]["values"]["dice"], [0.0, 0.25, 1.0])
        self.assertEqual(full["paired_counts"], {"l2_higher": 1, "equal": 2, "l1_higher": 0})
        self.assertEqual(result["cohorts"]["small"]["ids"], self.small_ids)
        self.assertEqual(result["cohorts"]["small"]["models"]["L2_GT"]["values"]["dice"], [1.0, 0.0])
        distribution = full["models"]["L2_CA2"]["distribution"]["precision"]
        self.assertEqual(distribution["quartiles"], [0.25, 0.5, 0.75])
        self.assertEqual(len(distribution["grid"]), 161)
        self.assertEqual(distribution["grid"][0], 0.0)
        self.assertEqual(distribution["grid"][-1], 1.0)
        self.assertEqual(max(distribution["density"]), 1.0)
        with (self.output / "source_data.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 4 * (len(self.full_ids) + len(self.small_ids)))
        self.assertEqual([row["pdb_id"] for row in rows[:3]], self.full_ids)
        self.assertEqual([row["pdb_id"] for row in rows[12:14]], self.small_ids)
        with (self.output / "bar_statistics.csv").open(encoding="utf-8-sig", newline="") as stream:
            bars = list(csv.DictReader(stream))
        self.assertEqual(len(bars), 24)
        for row in bars:
            stats = result["cohorts"][row["cohort"]]["models"][row["method"]]["bars"][row["metric"]]
            self.assertEqual(float(row["mean"]), stats["mean"])
            self.assertEqual(float(row["ci95_lower"]), stats["lower"])
            self.assertEqual(float(row["ci95_upper"]), stats["upper"])

    def test_shared_bootstrap_indices_match_reference(self):
        prepare_plot_data(self.l2_path, self.l1_root, self.manifest, self.output)
        full = json.loads((self.output / "plot_data.json").read_text(encoding="utf-8"))["cohorts"]["full"]
        columns = [(method, metric) for method in METHODS for metric in METRICS[:3]]
        matrix = np.column_stack([full["models"][method]["values"][metric] for method, metric in columns])
        rng = np.random.default_rng(BOOTSTRAP_SEED)
        indices = rng.integers(0, 3, size=(BOOTSTRAP_REPLICATES, 3))
        bounds = np.quantile(matrix[indices].mean(axis=1), [0.025, 0.975], axis=0)
        for index, (method, metric) in enumerate(columns):
            stats = full["models"][method]["bars"][metric]
            self.assertEqual(stats["mean"], float(matrix[:, index].mean()))
            self.assertEqual(stats["lower"], float(bounds[0, index]))
            self.assertEqual(stats["upper"], float(bounds[1, index]))

    def test_order_mismatch_fails_before_publication(self):
        self.l2["models"]["GT"]["full_rows"].reverse()
        self.l2_path.write_text(json.dumps(self.l2), encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "PDB membership/order mismatch"):
            prepare_plot_data(self.l2_path, self.l1_root, self.manifest, self.output)
        self.assertFalse(self.output.exists())

    def test_missing_member_fails_before_publication(self):
        self.l2["models"]["GT"]["full_rows"].pop()
        self.l2_path.write_text(json.dumps(self.l2), encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "PDB membership/order mismatch"):
            prepare_plot_data(self.l2_path, self.l1_root, self.manifest, self.output)
        self.assertFalse(self.output.exists())

    def test_invalid_frozen_metric_fails_before_publication(self):
        self.l2["models"]["GT"]["full_rows"][0]["semantic_macro_f1"] = float("nan")
        self.l2_path.write_text(json.dumps(self.l2), encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "invalid frozen metric"):
            prepare_plot_data(self.l2_path, self.l1_root, self.manifest, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_output_is_not_overwritten(self):
        self.output.mkdir()
        (self.output / "plot_data.json").write_bytes(b"existing frozen output")
        with self.assertRaisesRegex(AssertionError, "Refusing to overwrite"):
            prepare_plot_data(self.l2_path, self.l1_root, self.manifest, self.output)
        self.assertEqual((self.output / "plot_data.json").read_bytes(), b"existing frozen output")
        self.assertFalse((self.output / "source_data.csv").exists())


if __name__ == "__main__":
    unittest.main()
