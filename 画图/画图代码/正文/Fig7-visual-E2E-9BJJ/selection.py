"""Fig7持有受控CA2作者病例的100%预算与原Top1选择, Fig8和三BACKUP显式复用.

read_case只读受控test0原traces和原排序评价; 合格成员沿用Fig6的唯一cohorts实现. 与实际全身份重计费曲线是不同科学职责, 不把本图规则放入TOOLS.
"""

from pathlib import Path
from TOOLS.runtime.paths import load_module

FIG6 = Path(__file__).resolve().parents[1] / "Fig6-result-E2E"
read_cohorts = load_module(FIG6 / "cohorts.py", "fig6_author_case_cohorts").read_cohorts


def read_case(store, pdb, include_background):
    """返回一个PDB的受控CA2原Top1、成功实例和无参考背景事实.

    store: SourceStore. pdb: str, 原小写PDB标识. include_background: bool, 完整BACKUP视图需要物化背景Top1时为True; 作者采用PNG的指标复核为False. 返回dict中的poses沿原traces顺序, sample_index是原采样编号, sdf_index是成功SDF位置, rmsd_A为原世界坐标RMSD(Å)或无合法参考时None.
    """
    _, members, _ = read_cohorts(store, False)
    eligible = members[pdb]
    budget = len(eligible)
    # /storage/penghongen/Adaligand_E2E/test/test_0/evaluation/CA2/evaluation.json: traces[pdb]逐候选保存attempt_index/source_blob_index/identity_correct/matched_occurrence_id/docking_stage, 例9bjj预算11, 路径/storage/penghongen/Adaligand_E2E/test/test_0/build/PocketXMol-tuned/CA2/test/local-c1/30ga/1, blob编号不等于occurrence.
    # 生产说明: /home/penghongen/Feedback/AdaLigand/releases/AdaLigand_0e2ed5a4829f/AdaLigand/ligandseek_pipeline/README.md; C:/Users/15919/Desktop/AdaLigand/ligandseek_pipeline/README.md. 合格成员来自Fig6/cohorts.py注明的原Matcher清单, 不按预测成功缩小分母.
    rows = store.json(
        "/storage/penghongen/Adaligand_E2E/test/test_0/evaluation/CA2/evaluation.json"
    )["traces"][pdb]
    # /storage/penghongen/Adaligand_E2E/actual_display_20261101/CA2/display_results.jsonl: 每行pdb_id/source_blob_index/status/output_dir/reference_rmsd_available; 30ga blob5的实际目录/storage/penghongen/Adaligand_E2E/actual_display_20261101/CA2/build/test/local-c1/30ga/5有背景姿态, 无合法参考RMSD, 不算成功.
    # 现存生产说明: /storage/penghongen/Adaligand_E2E/actual_display_20261101/control/releases/AdaLigand_e15f82b50271/AdaLigand/ligandseek_pipeline/README.md; 当前本地阅读入口C:/Users/15919/Desktop/AdaLigand/ligandseek_pipeline/README_Build.md.
    actual = store.json(
        "/storage/penghongen/Adaligand_E2E/actual_display_20261101/CA2/display_results.jsonl"
    )
    actual_by_key = {(row["pdb_id"], row["source_blob_index"]): row for row in actual}
    charged = [
        row for row in rows if row["attempt_index"] is not None and row["attempt_index"] <= budget
    ]
    chosen = []
    for row in charged:
        valid = row["identity_correct"] and row["matched_occurrence_id"] in eligible
        stage = (
            row["docking_stage"]
            if valid
            else actual_by_key.get((pdb, row["source_blob_index"])) if include_background else None
        )
        if stage and stage["status"] == "success":
            chosen.append((row, valid, stage["output_dir"]))
    # /storage/penghongen/Adaligand_E2E/test/test_0/build/PocketXMol-tuned/CA2/test/local-c1/<pdb>/<blob>/{ranking.json,evaluation_metrics.json}: ranking.top1_sample_index给原模型首位; metrics按sample_index连接rmsd_A和sdf_index. 背景来源由上述actual索引给出, 如30ga/5, 不凭路径拼接.
    # 两类生产README分别在上面0e2ed5a4829f和actual_display e15f82b50271 release; 不用真实RMSD重选原Top1.
    store.read_many(
        [
            source + "/" + name
            for _, _, source in chosen
            for name in ["ranking.json", "evaluation_metrics.json"]
        ]
    )
    poses = []
    for row, valid, source in chosen:
        ranking = store.json(source + "/ranking.json")
        metric = next(
            item
            for item in store.json(source + "/evaluation_metrics.json")
            if item["sample_index"] == ranking["top1_sample_index"]
        )
        rmsd = metric["rmsd_A"] if valid else None
        poses.append(
            dict(
                occurrence_id=row["matched_occurrence_id"],
                source_blob_index=row["source_blob_index"],
                sample_index=ranking["top1_sample_index"],
                sdf_index=metric["sdf_index"],
                rmsd_A=rmsd,
                server_output=source,
                eligible_identity=valid,
                success=bool(valid and rmsd is not None and rmsd < 2),
            )
        )
    successes = {pose["occurrence_id"] for pose in poses if pose["success"]}
    valid_rmsd = [
        pose["rmsd_A"] for pose in poses if pose["eligible_identity"] and pose["rmsd_A"] is not None
    ]
    return dict(
        pdb=pdb,
        receptor="CA2",
        budget=budget,
        pose="model Top-1",
        rmsd_cutoff_A=2,
        success_count=len(successes),
        target_count=budget,
        valid_pose_count=sum(pose["eligible_identity"] for pose in poses),
        predicted_pose_count=len(poses),
        rmsd_range_A=[min(valid_rmsd), max(valid_rmsd)],
        poses=poses,
        additional_no_reference=[
            dict(blob=row["source_blob_index"], server_output=row["output_dir"])
            for row in actual
            if row["pdb_id"] == pdb
            and row["source_blob_index"] in {r["source_blob_index"] for r in charged}
            and row["status"] == "success"
            and not row["reference_rmsd_available"]
        ],
    )
