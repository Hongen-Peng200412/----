#!/usr/bin/env python3
"""Emap2lig CLI and programmatic inference API."""

import csv
import shutil
import uuid
from pathlib import Path

import numpy as np
import torch
import yaml
from hydra import compose, initialize_config_dir
from hydra.utils import instantiate
from lightning import Trainer, seed_everything
from loguru import logger
from rdkit import Chem
from skimage import measure
from torch.utils.data import DataLoader
import typer

import rdkit
from huggingface_hub import hf_hub_download

from emap2lig.data.ccd import CCDFetchError, get_ccd_mol, get_conformer_from_smiles
from emap2lig.data.const import bond_type_ids, chirality_type_ids
from emap2lig.data.dataset import LigandModelingDataset, collate_fn
from emap2lig.data.io.map import parse_mrc, to_mrc
from emap2lig.data.io.writer import LigandWriter
from emap2lig.data.map import get_unified_mrc
from emap2lig.data.types import (
    Atom,
    Bond,
    DensityObject,
    LigandObject,
    LigandRecord,
    MapObject,
)

# ---------------------------------------------------------------------------
# Model weights directory & metadata
# ---------------------------------------------------------------------------
MODEL_DIR = Path.home() / ".emap2lig" / "models"
REPO_ID = "KiharaLab/Emap2lig"
MODEL_FILES: dict[str, str] = {
    "detection_model": "emap2lig-find-v0.0.1.safetensors",
    "structure_model": "emap2lig-build-v0.0.1.safetensors",
}

# Set default pickle properties
pickle_option = rdkit.Chem.PropertyPickleOptions.AllProps
rdkit.Chem.SetDefaultPickleProperties(pickle_option)

if torch.cuda.is_available():
    torch.set_float32_matmul_precision("high")
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch._dynamo.config.cache_size_limit = 2048
    torch._dynamo.config.accumulated_cache_size_limit = 2048
    torch.autograd.set_detect_anomaly(True)


def _require_cuda_gpu(gpu: int) -> None:
    """Validate that a usable CUDA GPU device ID is provided."""
    if gpu < 0:
        raise ValueError(
            "CPU inference is not supported. Please provide --gpu with a CUDA "
            "device ID (0..N-1)."
        )
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available in this environment. Emap2lig requires an "
            "NVIDIA GPU (CUDA 12/13)."
        )
    device_count = torch.cuda.device_count()
    if gpu >= device_count:
        raise ValueError(
            f"Invalid GPU device ID {gpu}. Available CUDA devices: 0..{device_count - 1}."
        )


# ---------------------------------------------------------------------------
# Model weight helpers — download to ~/.emap2lig/models/
# ---------------------------------------------------------------------------


def get_model_path(filename: str) -> Path:
    """Return the expected local path for a model weight file.

    Parameters
    ----------
    filename : str
        Relative filename inside the HuggingFace repo
        (e.g. ``"emap2lig-find-v0.0.1.safetensors"``).

    Returns
    -------
    Path
        ``~/.emap2lig/models/<filename>``.
    """
    return MODEL_DIR / filename


def check_weights() -> dict[str, bool]:
    """Check which model weights are already downloaded.

    Returns
    -------
    dict[str, bool]
        Mapping of model key → whether the file exists locally.
    """
    return {key: get_model_path(fn).exists() for key, fn in MODEL_FILES.items()}


def download_weights(
    repo_id: str = REPO_ID,
    filename: str | None = None,
) -> Path:
    """Download a single weight file to ``~/.emap2lig/models/``.

    If *filename* is ``None``, all known model files are downloaded.

    Parameters
    ----------
    repo_id : str
        HuggingFace repository ID.
    filename : str | None
        Relative path inside the repo. When ``None`` every file in
        :data:`MODEL_FILES` is downloaded.

    Returns
    -------
    Path
        Path to the downloaded file (or :data:`MODEL_DIR` when downloading all).
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    if filename is None:
        for fn in MODEL_FILES.values():
            download_weights(repo_id=repo_id, filename=fn)
        return MODEL_DIR

    local_path = get_model_path(filename)
    if local_path.exists():
        logger.info(f"Weights already present at {local_path}")
        return local_path

    logger.info(f"Downloading {repo_id}/{filename} → {local_path}")
    hf_hub_download(repo_id=repo_id, filename=filename, local_dir=str(MODEL_DIR))
    return local_path


def ensure_weights() -> None:
    """Download all model weights if not already present."""
    status = check_weights()
    if all(status.values()):
        logger.info("All model weights present.")
        return
    for key, present in status.items():
        if not present:
            fn = MODEL_FILES[key]
            logger.info(f"Missing {key} ({fn}), downloading...")
            download_weights(filename=fn)


def save_ligand_blobs(
    ligand_mask_obj: MapObject,
    unified_obj: MapObject,
    blobs_dir: Path,
    min_spatial_size: int,
) -> tuple[int, int]:
    """按官方连通域顺序裁剪并写出全部达到面积门槛的配体实例.

    输入参数:
        - ligand_mask_obj: MapObject, ``grid_data`` 为 ``(D, H, W)`` 的 Li 二值掩码; 三个数组轴依次为 Z、Y、X, ``global_origin`` 和 ``voxel_size`` 按 X、Y、Z 排列, 单位 Å.
        - unified_obj: MapObject, ``grid_data`` 为与 Li 掩码处于同一体素网格的 ``(D, H, W)`` 统一密度图; 数组轴依次为 Z、Y、X.
        - blobs_dir: Path, 实例产物目录; 调用前必须已经存在.
        - min_spatial_size: int, 每个空间维度的最小裁剪长度; 官方 Find 使用 48.

    返回值:
        - saved_blob_count: int, 面积不少于 32 个体素并已写出的实例数量; 同时是最大的 ``blob_N`` 编号.
        - raw_component_count: int, ``measure.label(..., connectivity=3)`` 产生的原始连通域数量; 包含面积小于 32 的连通域.

    落盘产物:
        - ``<blobs_dir>/blob_N.npz``: ``DensityObject``; ``density_grid`` 和 ``instance_grid`` 均为 ``(D_crop, H_crop, W_crop)``, ``global_origin`` 与 ``voxel_size`` 按 X、Y、Z 排列.
        - ``<blobs_dir>/mask_N.mrc``: MRC; 保存与 ``blob_N.npz.instance_grid`` 逐体素一致的实例掩码及同一原点和体素尺寸.

    等价边界:
        - 连通域定义、遍历顺序、32 体素过滤和保留实例编号沿用官方实现.
        - 裁剪起止位置严格复现 ``crop_mrcs(..., pad_mode="symmetric", extended_val=0)``; 左侧越界通过移动裁剪起点补偿, 右侧越界只在数组尾部补零.
        - 本函数只用 ``prop.bbox`` 和局部 ``prop.image`` 构造实例掩码, 不为每个实例分配或扫描完整 ``(D, H, W)`` 数组.
    """

    if not np.allclose(ligand_mask_obj.global_origin, unified_obj.global_origin):
        raise ValueError("All MRC objects must have the same global origin.")

    # (D, H, W), 26 邻域连通域标签; 0 表示背景, 正整数按 skimage 的官方顺序标识 Li 实例.
    labeled_mask = measure.label(ligand_mask_obj.grid_data, connectivity=3)
    logger.info(f"Found {np.max(labeled_mask)} objects in the ligand mask")

    # 每个 RegionProperties 对应一个原始连通域, 顺序决定过滤后的 blob_N 编号.
    props = measure.regionprops(labeled_mask)
    saved_blob_count = 0
    for prop in props:
        if prop.area < 32:
            continue

        saved_blob_count += 1
        logger.info(f"Cropping object {saved_blob_count} with unified map")

        # 三元素列表, 当前连通域在完整 ZYX 网格中的半开区间起点和终点.
        component_min_indices = [int(index) for index in prop.bbox[:3]]
        component_max_indices = [int(index) for index in prop.bbox[3:]]
        # 三元素列表, 当前连通域包围框在 Z、Y、X 三轴上的长度.
        content_size = [
            end - start
            for start, end in zip(
                component_min_indices,
                component_max_indices,
                strict=False,
            )
        ]
        # 三元素列表, 每轴达到 min_spatial_size 尚需补充的体素数.
        needed_padding = [
            max(0, min_spatial_size - size) for size in content_size
        ]
        # 三元素列表, 官方 symmetric 模式把奇数补零量的多一个体素放在右侧.
        pad_left = [pad_size // 2 for pad_size in needed_padding]
        pad_right = [
            pad_size - left
            for pad_size, left in zip(needed_padding, pad_left, strict=False)
        ]
        # 三元素列表, 完整 ZYX 网格中的裁剪起点; 左侧越界时固定为 0.
        final_start_indices = [
            max(0, start - left)
            for start, left in zip(
                component_min_indices,
                pad_left,
                strict=False,
            )
        ]
        # 三元素元组, 最终实例数组的 ZYX 形状; 每轴等于 max(连通域包围框长度, min_spatial_size).
        target_shape = tuple(
            content_size[axis] + pad_left[axis] + pad_right[axis]
            for axis in range(3)
        )
        # 三元素列表, 完整 ZYX 网格中的请求裁剪终点; 可以超过完整网格边界, 超出部分在尾部补零.
        final_end_indices = [
            start + target_shape[axis]
            for axis, start in enumerate(final_start_indices)
        ]

        if any(needed_padding):
            logger.warning(
                f"Padding required: shape {content_size} -> minimum {min_spatial_size}"
            )

        # float32, (3,), 裁剪起点的 XYZ 体素偏移; 反转是因为数组轴为 ZYX, 空间元数据为 XYZ.
        bbox_xyz_start = np.array(final_start_indices[::-1], dtype=np.float32)
        # (3,), 裁剪后数组中索引 (0, 0, 0) 对应的 XYZ 世界坐标, 单位 Å.
        final_origin = ligand_mask_obj.global_origin + np.multiply(
            bbox_xyz_start,
            ligand_mask_obj.voxel_size,
        )

        # 三个 slice, 在统一密度图边界内截取请求的 ZYX 半开区间.
        density_bbox = tuple(
            slice(
                min(final_start_indices[axis], unified_obj.grid_data.shape[axis]),
                min(final_end_indices[axis], unified_obj.grid_data.shape[axis]),
            )
            for axis in range(3)
        )
        # 与 unified_obj 相同的数据类型, (D_valid, H_valid, W_valid), 请求裁剪与完整密度图的有效交集.
        density_grid = unified_obj.grid_data[density_bbox]
        if density_grid.shape != target_shape:
            # 三个二元组, 仅在每轴尾部补齐超出完整密度图的请求体素.
            density_pad_width = tuple(
                (0, target_shape[axis] - density_grid.shape[axis])
                for axis in range(3)
            )
            density_grid = np.pad(
                density_grid,
                density_pad_width,
                mode="constant",
                constant_values=0,
            )

        # uint8, (D_crop, H_crop, W_crop), 当前实例的局部 0/1 掩码; 轴顺序为 ZYX.
        instance_grid = np.zeros(target_shape, dtype=np.uint8)
        # 三元素列表, prop.image 的 ZYX 起点在局部实例数组中的偏移.
        component_local_start = [
            component_min_indices[axis] - final_start_indices[axis]
            for axis in range(3)
        ]
        # 三个 slice, 把紧致包围框 prop.image 放入局部实例数组的对应 ZYX 区间.
        component_local_bbox = tuple(
            slice(
                component_local_start[axis],
                component_local_start[axis] + prop.image.shape[axis],
            )
            for axis in range(3)
        )
        instance_grid[component_local_bbox] = prop.image

        # MapObject, 保存 mask_N.mrc 所需的局部掩码、XYZ 原点和 XYZ 体素尺寸.
        instance_map = MapObject(
            grid_data=instance_grid,
            voxel_size=ligand_mask_obj.voxel_size,
            global_origin=final_origin,
        )
        # DensityObject, blob_N.npz 的五个官方字段; 两个三维数组逐体素对齐.
        ligand_density_object = DensityObject(
            object_id=saved_blob_count,
            density_grid=density_grid,
            instance_grid=instance_grid,
            global_origin=final_origin,
            voxel_size=unified_obj.voxel_size,
        )

        blob_path = blobs_dir / f"blob_{saved_blob_count}.npz"
        ligand_density_object.dump(blob_path)
        logger.info(f"Saved blob {saved_blob_count} to {blob_path}")

        mask_path = blobs_dir / f"mask_{saved_blob_count}.mrc"
        logger.info(f"Saving mask {saved_blob_count} to {mask_path}")
        to_mrc(instance_map, mask_path, verbose=False)

    logger.info(f"Saved {saved_blob_count} blobs to {blobs_dir}")
    return saved_blob_count, len(props)


def detect_ligand_objects(
    input_map: Path | str,
    output_dir: Path | str,
    cfg: object,
    emdb_id: str | None = None,
) -> tuple[int, Path | None]:
    """Detect ligand objects in cryo-EM density maps using Emap2lig.

    Args:
        input_map: Path to input cryo-EM map file.
        output_dir: Directory to save output files.
        cfg: Hydra configuration object.
        emdb_id: EMDB ID for the map (optional).

    Returns:
        Tuple of (status_code, blobs_dir).  *status_code* is 0 for
        success, 1 for failure.  *blobs_dir* is ``None`` on failure.
    """
    try:
        # Create paths
        input_path = Path(input_map)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        map_stem = str(input_path.stem).split(".")[0]
        logger.info(f"Map stem: {map_stem}")

        # Enforce GPU-only inference for detection.
        _require_cuda_gpu(int(cfg.gpu))

        detection_spatial_size = int(cfg.detection_model.spatial_size)
        structure_spatial_size = int(cfg.spatial_size)

        # Output file paths/directories
        preprocess_dir = output_dir / "preprocess"
        preprocess_dir.mkdir(parents=True, exist_ok=True)
        find_maps_dir = output_dir / "find_maps"
        find_maps_dir.mkdir(parents=True, exist_ok=True)
        blobs_dir = output_dir / "find_blobs"
        blobs_dir.mkdir(parents=True, exist_ok=True)

        unified_map_path = preprocess_dir / "unified.mrc"
        detection_labels = list(cfg.detection_labels)
        if not detection_labels:
            raise ValueError("cfg.detection_labels must define at least one label")
        if "ligand" not in detection_labels:
            raise ValueError("cfg.detection_labels must include 'ligand'")
        label_map_paths = {
            label: find_maps_dir / f"{label}.mrc" for label in detection_labels
        }
        label_mask_paths = {
            label: find_maps_dir / f"{label}_mask.mrc" for label in detection_labels
        }
        ligand_map_path = label_map_paths["ligand"]
        ligand_mask_path = label_mask_paths["ligand"]

        # Parse input map
        logger.info(f"Loading cryo-EM map from {input_path}")
        raw_obj = parse_mrc(input_path, emdb_id=emdb_id)
        unified_obj = get_unified_mrc(
            raw_obj,
            min_spatial_size=detection_spatial_size,
            extended_val=cfg.extended_val,
            contour_level=cfg.contour_level,
        )
        to_mrc(unified_obj, unified_map_path, verbose=False)

        missing_label_map = [
            label for label in detection_labels if not label_map_paths[label].exists()
        ]
        missing_label_mask = [
            label for label in detection_labels if not label_mask_paths[label].exists()
        ]

        if missing_label_map or missing_label_mask:
            # Convert map to tensor
            input_map_tensor = torch.from_numpy(unified_obj.grid_data).float()
            # Add batch and channel dimensions
            input_map_tensor = input_map_tensor.unsqueeze(0).unsqueeze(
                0
            )  # [1, 1, D, H, W]

            # Initialize model from config
            logger.info("Initializing Emap2lig model from configuration")
            detection_model = instantiate(cfg.detection_model)

            # Set device
            device = torch.device(
                f"cuda:{cfg.gpu}"
                if torch.cuda.is_available() and cfg.gpu >= 0
                else "cpu"
            )
            output_device = torch.device("cpu")

            # Run ligand detection
            logger.info(f"Running ligand detection on device: {device}")
            predicted_map = detection_model.sliding_window_inference(
                input_map=input_map_tensor,
                roi_size=detection_spatial_size,
                batch_size=cfg.detection_batch_size,
                device=device,
                output_device=output_device,
            )

            if predicted_map.shape[1] < len(detection_labels):
                raise ValueError(
                    "Detection output has fewer channels than configured labels: "
                    f"{predicted_map.shape[1]} < {len(detection_labels)}"
                )

            binary_map, channel_thresholds = detection_model._binarize_output(
                predicted_map
            )
            if "ligand" in channel_thresholds:
                logger.info(
                    f"Ligand detection threshold: {channel_thresholds['ligand']:.6f}"
                )

            ligand_mask_obj = None

            for channel_idx, label in enumerate(detection_labels):
                label_map = predicted_map[:, channel_idx : channel_idx + 1, ...]
                label_mask = binary_map[:, channel_idx : channel_idx + 1, ...]
                label_mask_np = label_mask.squeeze(0).squeeze(0).numpy()

                # ligand 全零仍保存模型真实概率与空掩码, 让零候选完整进入评价; 其他通道沿用旧写出行为.
                if np.count_nonzero(label_mask_np) == 0 and label != "ligand":
                    logger.info(
                        f"Skipping {label} map/mask save: binarized map is all zero"
                    )
                    continue

                label_map_np = label_map.squeeze(0).squeeze(0).numpy()
                label_map_obj = MapObject(
                    grid_data=label_map_np,
                    voxel_size=unified_obj.voxel_size,
                    global_origin=unified_obj.global_origin,
                    emdb_id=unified_obj.emdb_id,
                )
                label_map_path = label_map_paths[label]
                logger.info(f"Saving {label} map to {label_map_path}")
                to_mrc(label_map_obj, label_map_path, verbose=False)

                label_mask_obj = MapObject(
                    grid_data=label_mask_np,
                    voxel_size=unified_obj.voxel_size,
                    global_origin=unified_obj.global_origin,
                    emdb_id=unified_obj.emdb_id,
                )
                label_mask_path = label_mask_paths[label]
                logger.info(f"Saving {label} mask to {label_mask_path}")
                to_mrc(label_mask_obj, label_mask_path, verbose=False)

                if label == "ligand":
                    ligand_mask_obj = label_mask_obj

            if ligand_mask_obj is None:
                raise RuntimeError("Failed to generate ligand mask object")

            logger.info("Ligand detection completed successfully")
        else:
            logger.info(
                f"All detection label maps/masks already exist under {find_maps_dir}"
            )
            # load the mask
            ligand_mask_obj = parse_mrc(ligand_mask_path)

            if not ligand_map_path.exists():
                logger.warning(f"Ligand map is missing at {ligand_map_path}")

        # Split the ligand mask into separate objects and save them
        logger.info("Splitting ligand mask into separate objects")
        saved_blob_count, raw_component_count = save_ligand_blobs(
            ligand_mask_obj=ligand_mask_obj,
            unified_obj=unified_obj,
            blobs_dir=blobs_dir,
            min_spatial_size=structure_spatial_size,
        )

        if saved_blob_count > 100:
            logger.warning(
                f"The detection contains {saved_blob_count} (more than 100) objects. Keeping all detected objects."
            )

        # Check if any objects were detected
        if raw_component_count == 0:
            logger.warning("No ligand blobs detected")
            # 推断完成但零检出是有效结果; 技术异常仍由下方异常分支返回 1 和 None.
            return 0, blobs_dir

        return 0, blobs_dir

    except (RuntimeError, ValueError, OSError) as e:
        logger.error(f"Error during ligand object detection: {e}")
        return 1, None


def convert_atom_name(name: str) -> tuple[int, int, int, int]:
    """Convert an atom name to a 4-element integer code (PDB convention).

    Each character is mapped to ``ord(c) - 32``; shorter names are
    zero-padded to length 4.

    Args:
        name: Atom name string (max 4 characters after stripping).

    Returns:
        4-tuple of integer character codes.

    Raises:
        ValueError: If the name exceeds 4 characters after stripping.
    """
    name = name.strip()
    name_code = [ord(c) - 32 for c in name]
    if len(name_code) > 4:
        raise ValueError(
            f"Atom name {name!r} exceeds 4 characters (got {len(name_code)})"
        )
    name_code = name_code + [0] * (4 - len(name_code))
    return tuple(name_code)  # type: ignore[return-value]


def _extract_atom_features(
    mol: Chem.Mol,
    residue_id: int = 1,
    auto_name: bool = False,
) -> tuple[list[tuple], list[str]]:
    """Extract atom features and names from an RDKit molecule.

    Args:
        mol: RDKit molecule (expected to have a conformer and atom
            ``name`` properties when *auto_name* is False).
        residue_id: Residue identifier stored in each atom record.
        auto_name: When True, atoms without a ``name`` property are
            assigned ``"<SYMBOL><INDEX>"`` (e.g. ``"C1"``).  When
            False, the name defaults to an empty string.

    Returns:
        Tuple of (atom_tuples, atom_names) where each atom tuple
        conforms to the :data:`Atom` structured-array dtype.
    """
    atom_tuples: list[tuple] = []
    atom_names: list[str] = []

    for atom_idx, atom in enumerate(mol.GetAtoms()):
        if atom.HasProp("name"):
            atom_name = atom.GetProp("name")
        elif auto_name:
            atom_name = f"{atom.GetSymbol()}{atom_idx + 1}"
        else:
            atom_name = ""

        atom_names.append(atom_name)

        name_code = convert_atom_name(atom_name)
        atomic_num = atom.GetAtomicNum()
        formal_charge = atom.GetFormalCharge()

        chirality_type = atom.GetChiralTag().name
        chirality_type_id = chirality_type_ids.get(chirality_type, 0)
        chirality_one_hot = [False] * 7
        chirality_one_hot[chirality_type_id] = True

        in_ring = [
            atom.IsInRingSize(3),
            atom.IsInRingSize(4),
            atom.IsInRingSize(5),
            atom.IsInRingSize(6),
        ]

        try:
            conformer = mol.GetConformer()
            pos = conformer.GetAtomPosition(atom.GetIdx())
            ref_pos = (pos.x, pos.y, pos.z)
        except ValueError:
            ref_pos = (0.0, 0.0, 0.0)

        atom_tuples.append(
            (
                name_code,
                atomic_num,
                formal_charge,
                (0.0, 0.0, 0.0),
                ref_pos,
                False,
                tuple(chirality_one_hot),
                tuple(in_ring),
                residue_id,
            )
        )

    return atom_tuples, atom_names


def _extract_bond_features(
    mol: Chem.Mol,
    atom_offset: int = 0,
) -> list[tuple]:
    """Extract bond features from an RDKit molecule.

    Args:
        mol: RDKit molecule.
        atom_offset: Offset added to atom indices (used when combining
            residues from a branched ligand).

    Returns:
        List of bond tuples conforming to the :data:`Bond` dtype.
    """
    bond_tuples: list[tuple] = []

    for bond in mol.GetBonds():
        begin_idx = bond.GetBeginAtomIdx() + atom_offset
        end_idx = bond.GetEndAtomIdx() + atom_offset

        bond_type = bond.GetBondType().name
        bond_type_id = bond_type_ids.get(bond_type, 0)
        bond_type_one_hot = [False] * 5
        if bond_type_id < 5:
            bond_type_one_hot[bond_type_id] = True

        in_ring = [
            bond.IsInRingSize(3),
            bond.IsInRingSize(4),
            bond.IsInRingSize(5),
            bond.IsInRingSize(6),
        ]

        bond_tuples.append(
            (
                begin_idx,
                end_idx,
                tuple(bond_type_one_hot),
                tuple(in_ring),
            )
        )

    return bond_tuples


def process_branched_ligand(
    branched_config: dict,
    ligand_name: str,
    ligands_dir: Path,
    blobs: list[int] | None = None,
) -> None:
    """Process a branched ligand configuration to create a LigandObject.

    Args:
        branched_config: Dictionary with ``residues`` and ``bonds`` keys.
        ligand_name: Name for the ligand (e.g. ``"LIG1"``).
        ligands_dir: Directory to save the output NPZ.
        blobs: List of blob IDs associated with this ligand.
    """
    # Extract residue information
    residue_list = branched_config.get("residues", [])
    inter_bonds = branched_config.get("bonds", [])

    # Parse residue names from the list (format: "1. NAG")
    residue_names = []
    for res_entry in residue_list:
        parts = res_entry.strip().split(".")
        if len(parts) >= 2:
            res_name = parts[1].strip()
            residue_names.append(res_name)

    logger.info(
        f"Processing branched ligand {ligand_name} with residues: {residue_names}"
    )

    all_atoms: list[tuple] = []
    all_bonds: list[tuple] = []
    atom_names: list[str] = []
    atom_offset = 0
    residue_atom_counts: list[int] = []

    for residue_idx, res_name in enumerate(residue_names, start=1):
        try:
            ref_mol = get_ccd_mol(res_name)
        except CCDFetchError as exc:
            logger.warning(f"Residue {res_name}: {exc}")
            continue
        ref_mol = Chem.RemoveHs(ref_mol, sanitize=False)

        residue_atoms, residue_atom_names = _extract_atom_features(
            ref_mol, residue_id=residue_idx, auto_name=True
        )
        all_atoms.extend(residue_atoms)
        atom_names.extend(residue_atom_names)
        residue_atom_counts.append(len(residue_atoms))

        residue_bonds = _extract_bond_features(ref_mol, atom_offset=atom_offset)
        all_bonds.extend(residue_bonds)

        atom_offset += len(residue_atoms)

    # Process inter-residue bonds
    for bond_info in inter_bonds:
        if len(bond_info) != 4:
            logger.warning(f"Invalid bond format: {bond_info}")
            continue

        res1_idx, atom1_name, res2_idx, atom2_name = bond_info

        # Convert to 0-based indices
        res1_idx -= 1
        res2_idx -= 1

        if res1_idx >= len(residue_atom_counts) or res2_idx >= len(residue_atom_counts):
            logger.warning(f"Invalid residue indices in bond: {bond_info}")
            continue

        # Find global atom indices
        # Calculate atom offset for each residue
        res1_offset = sum(residue_atom_counts[:res1_idx])
        res2_offset = sum(residue_atom_counts[:res2_idx])

        # Find atom indices within residues (simplified - assumes atom names are unique)
        atom1_idx = None
        atom2_idx = None

        # Search for atoms in the respective residues
        for i in range(residue_atom_counts[res1_idx]):
            if atom_names[res1_offset + i] == atom1_name:
                atom1_idx = res1_offset + i
                break

        for i in range(residue_atom_counts[res2_idx]):
            if atom_names[res2_offset + i] == atom2_name:
                atom2_idx = res2_offset + i
                break

        if atom1_idx is not None and atom2_idx is not None:
            # Inter-residue bonds are typically single bonds
            bond_type_one_hot = [True, False, False, False, False]  # SINGLE
            in_ring = [False, False, False, False]

            all_bonds.append(
                (
                    atom1_idx,
                    atom2_idx,
                    tuple(bond_type_one_hot),
                    tuple(in_ring),
                )
            )
        else:
            logger.warning(f"Could not find atoms for bond: {bond_info}")

    # Create structured arrays
    atoms = np.array(all_atoms, dtype=Atom)
    bonds = np.array(all_bonds, dtype=Bond)

    # Create LigandObject
    ref_mol_object = LigandObject(
        smiles="",
        atom_names=atom_names,
        atoms=atoms,
        bonds=bonds,
        name=ligand_name,  # Use ligand name (LIG1, LIG2, etc.)
        residue_names=residue_names,  # Actual residue names (NAG, NAG, etc.)
        symmetries=[],  # No symmetries for branched ligands
        blobs=blobs,
    )

    # Save to NPZ file
    output_path = ligands_dir / f"{ligand_name}.npz"
    ref_mol_object.dump(output_path)
    logger.info(f"Saved branched molecular object for {ligand_name} to {output_path}")


def parse_ligand_list(ligand_list_path: Path | str) -> list[LigandRecord]:
    """Parse a ligand list file into a list of LigandRecord objects.

    Supports YAML (list or single-item), and plain text with
    ``CCD:`` or ``SMILES:`` prefixes.

    Args:
        ligand_list_path: Path to the ligand list file.

    Returns:
        Parsed ligand records.  Empty list on unsupported format.
    """
    ligand_records: list[LigandRecord] = []

    with open(ligand_list_path) as f:
        content = f.read().strip()

    # Try to parse as YAML first
    try:
        yaml_data = yaml.safe_load(content)

        # Handle both single item and list cases
        if isinstance(yaml_data, list):
            items_to_process = yaml_data
        elif yaml_data is not None:
            # Single item case - wrap in a list
            items_to_process = [yaml_data]
        else:
            # Empty YAML or null
            items_to_process = []

        lig_counter = 0  # Unified counter for naming non-CCD ligands

        for item in items_to_process:
            if isinstance(item, dict):
                if "BRANCHED" in item:
                    # Handle BRANCHED dictionary
                    branched_config = item["BRANCHED"]
                    blob_ids = item.get("blob_id", item.get("blobs", None))
                    if blob_ids is not None and not isinstance(blob_ids, list):
                        blob_ids = [blob_ids]

                    # Extract residues and bonds from branched config
                    residue_list = branched_config.get("residues", [])
                    inter_bonds = branched_config.get("bonds", [])

                    # Parse residue names from the list (format: "1. NAG")
                    residues = {}
                    for i, res_entry in enumerate(residue_list, start=1):
                        parts = res_entry.strip().split(".")
                        if len(parts) >= 2:
                            res_name = parts[1].strip()
                            residues[i] = res_name

                    lig_counter += 1
                    ligand_records.append(
                        LigandRecord(
                            type="BRANCHED",
                            name=f"LIG{lig_counter}",
                            blobs=blob_ids,
                            residues=residues,
                            bonds=inter_bonds,
                        )
                    )
                elif "CCD" in item:
                    # Handle CCD dictionary format
                    ccd_code = item["CCD"]
                    blob_ids = item.get("blob_id", item.get("blobs", None))
                    if blob_ids is not None and not isinstance(blob_ids, list):
                        blob_ids = [blob_ids]

                    ligand_records.append(
                        LigandRecord(
                            type="CCD",
                            name=ccd_code,
                            blobs=blob_ids,
                        )
                    )
                elif "SMILES" in item:
                    # Handle SMILES dictionary format
                    smiles_string = item["SMILES"]
                    blob_ids = item.get("blob_id", item.get("blobs", None))
                    if blob_ids is not None and not isinstance(blob_ids, list):
                        blob_ids = [blob_ids]

                    lig_counter += 1
                    ligand_records.append(
                        LigandRecord(
                            type="SMILES",
                            name=f"LIG{lig_counter}",
                            blobs=blob_ids,
                            smiles=smiles_string,
                        )
                    )
                else:
                    logger.warning(f"Unrecognized dictionary format in list: {item}")
            elif isinstance(item, str):
                # Handle CCD: or SMILES: strings
                if item.startswith("CCD:"):
                    ccd_code = item.split(":", 1)[1].strip()
                    ligand_records.append(
                        LigandRecord(
                            type="CCD",
                            name=ccd_code,
                        )
                    )
                elif item.startswith("SMILES:"):
                    smiles_string = item.split(":", 1)[1].strip()
                    lig_counter += 1
                    ligand_records.append(
                        LigandRecord(
                            type="SMILES",
                            name=f"LIG{lig_counter}",
                            smiles=smiles_string,
                        )
                    )
                else:
                    logger.warning(f"Unrecognized string format in list: {item}")
            else:
                logger.warning(f"Unrecognized item format in list: {item}")

        return ligand_records

    except yaml.YAMLError:
        # If YAML parsing fails, try to parse as plain text
        logger.info(
            f"YAML parsing failed, trying plain text format for {ligand_list_path}"
        )

    # Handle plain text files with single ligand specification
    content_lines = [line.strip() for line in content.split("\n") if line.strip()]

    if len(content_lines) == 1:
        line = content_lines[0]
        if line.startswith("CCD:"):
            ccd_code = line.split(":", 1)[1].strip()
            ligand_records.append(
                LigandRecord(
                    type="CCD",
                    name=ccd_code,
                )
            )
            return ligand_records
        elif line.startswith("SMILES:"):
            smiles_string = line.split(":", 1)[1].strip()
            ligand_records.append(
                LigandRecord(
                    type="SMILES",
                    name="LIG1",
                    smiles=smiles_string,
                )
            )
            return ligand_records

    # If we get here, the format is not supported
    logger.error(
        f"Unsupported file format for {ligand_list_path}. "
        f"Supported formats: YAML files with lists/single items, or plain text with single CCD:/SMILES: entry."
    )
    return []


def prepare_CCD_data(ligand_record: LigandRecord, ligands_dir: Path) -> str | None:
    """
    Process a CCD ligand record to create a LigandObject.

    Args:
        ligand_record: CCD ligand record
        ligands_dir: Directory to save the output

    Returns:
        Ligand name if successful, None if failed
    """
    ligand_name = ligand_record.name
    logger.info(f"Processing CCD ligand {ligand_name}")

    try:
        ref_mol = get_ccd_mol(ligand_name)
    except CCDFetchError as exc:
        logger.warning(f"Ligand {ligand_name}: {exc}")
        return None

    try:
        # Generate SMILES
        smiles = Chem.MolToSmiles(ref_mol)

        # Remove hydrogens for processing
        ref_mol = Chem.RemoveHs(ref_mol, sanitize=False)

        # Process the molecule
        process_molecule(ref_mol, ligand_name, smiles, ligands_dir, ligand_record.blobs)
        return ligand_name

    except Exception as e:
        logger.error(f"Error processing CCD ligand {ligand_name}: {e}")
        return None


def prepare_SMILES_data(ligand_record: LigandRecord, ligands_dir: Path) -> str | None:
    """
    Process a SMILES ligand record to create a LigandObject.

    Args:
        ligand_record: SMILES ligand record
        ligands_dir: Directory to save the output

    Returns:
        Ligand name if successful, None if failed
    """
    ligand_name = ligand_record.name
    smiles = ligand_record.smiles

    if not smiles:
        logger.error(f"No SMILES string provided for ligand {ligand_name}")
        return None

    logger.info(f"Processing SMILES ligand as {ligand_name}: {smiles}")

    try:
        # Get conformer from SMILES
        result, ref_mol = get_conformer_from_smiles(smiles)

        if result == "failed":
            logger.warning(f"Failed to generate conformer for SMILES: {smiles}")
            return None

        # Process the molecule
        process_molecule(ref_mol, ligand_name, smiles, ligands_dir, ligand_record.blobs)
        return ligand_name

    except Exception as e:
        logger.error(f"Error processing SMILES ligand {ligand_name}: {e}")
        return None


def prepare_BRANCHED_data(ligand_record: LigandRecord, ligands_dir: Path) -> str | None:
    """
    Process a branched ligand record to create a LigandObject.

    Args:
        ligand_record: BRANCHED ligand record
        ligands_dir: Directory to save the output

    Returns:
        Ligand name if successful, None if failed
    """
    ligand_name = ligand_record.name
    residues = ligand_record.residues or {}
    bonds = ligand_record.bonds or []

    logger.info(
        f"Processing branched ligand {ligand_name} with residues: {list(residues.values())}"
    )

    # Convert to the format expected by process_branched_ligand
    branched_config = {
        "residues": [f"{idx}. {res_name}" for idx, res_name in residues.items()],
        "bonds": bonds,
    }

    try:
        process_branched_ligand(
            branched_config, ligand_name, ligands_dir, ligand_record.blobs
        )
        return ligand_name
    except Exception as e:
        logger.error(f"Error processing branched ligand {ligand_name}: {e}")
        return None


def prepare_ligand_dataset(
    ligand_records: list[LigandRecord],
    output_dir: Path,
    ligands_dir: Path | None = None,
) -> tuple[int, Path]:
    """
    Prepare a dataset of ligands for structure modeling.

    Args:
        ligand_records: List of ligand records to process
        output_dir: Root output directory
        ligands_dir: If provided, write ligand NPZ files here instead of the
            default ``output_dir/preprocess/ligands``.  Useful for incremental
            runs that must not pick up ligands from earlier runs.

    Returns:
        Tuple of (status_code, ligands_dir)
    """
    if ligands_dir is None:
        ligands_dir = output_dir / "preprocess" / "ligands"
    ligands_dir.mkdir(parents=True, exist_ok=True)

    # Process each ligand
    processed_ligands = []

    for record in ligand_records:
        if record.type == "BRANCHED":
            result = prepare_BRANCHED_data(record, ligands_dir)
        elif record.type == "CCD":
            result = prepare_CCD_data(record, ligands_dir)
        elif record.type == "SMILES":
            result = prepare_SMILES_data(record, ligands_dir)
        else:
            logger.warning(f"Unrecognized ligand record type: {record.type}")
            continue

        if result is not None:
            processed_ligands.append(result)

    logger.info(f"Successfully processed {len(processed_ligands)} ligands")
    return 0, ligands_dir


def process_molecule(
    ref_mol: Chem.Mol,
    ligand_name: str,
    smiles: str,
    ligands_dir: Path,
    blobs: list[int] | None = None,
) -> None:
    """Process a molecule to create a LigandObject and save it.

    Args:
        ref_mol: RDKit molecule object.
        ligand_name: Name for the ligand.
        smiles: SMILES string for the ligand.
        ligands_dir: Directory to save the output NPZ.
        blobs: List of blob IDs associated with this ligand.
    """
    atoms_list, atom_names = _extract_atom_features(ref_mol, residue_id=1)
    bonds_list = _extract_bond_features(ref_mol)

    atoms = np.array(atoms_list, dtype=Atom)
    bonds = np.array(bonds_list, dtype=Bond)

    ref_mol_object = LigandObject(
        smiles=smiles,
        atom_names=atom_names,
        atoms=atoms,
        bonds=bonds,
        name=ligand_name,  # Use ligand name (LIG1, LIG2, etc. for SMILES/BRANCHED, CCD code for CCD)
        residue_names=[ligand_name],
        symmetries=[],
        blobs=blobs,
    )

    # Save to NPZ file
    output_path = ligands_dir / f"{ligand_name}.npz"
    ref_mol_object.dump(output_path)
    logger.info(f"Saved reference molecular object for {ligand_name} to {output_path}")


def create_blob_csv_tables(outputs_dir: Path) -> None:
    """Sort per-blob CSV files by score and update the ``best/`` directory.

    The writer already appends rows to each blob's CSV during inference.
    This function re-reads those CSVs, sorts them by ``consistency_iou``
    descending, writes them back, and copies the highest-scoring CIF into
    ``best/``.

    Args:
        outputs_dir: Directory containing blob subdirectories with CSV/CIF files.
    """
    logger.info("Creating CSV tables for blob results")

    best_dir = outputs_dir / "best"
    best_dir.mkdir(exist_ok=True)
    logger.info(f"Created best results directory: {best_dir}")

    blob_dirs = [
        d for d in outputs_dir.iterdir() if d.is_dir() and d.name.startswith("blob_")
    ]

    for blob_dir in blob_dirs:
        logger.info(f"Processing {blob_dir.name}")

        csv_file = blob_dir / f"{blob_dir.name}_results.csv"

        # Read existing CSV rows
        scores: dict[str, float] = {}
        if csv_file.exists():
            try:
                with open(csv_file) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row["conformer_name"]
                        try:
                            scores[name] = float(row["consistency_iou"])
                        except (KeyError, ValueError):
                            pass
            except OSError as e:
                logger.warning(f"Failed to read CSV {csv_file}: {e}")

        # Safety net: include any CIF files that somehow lack a CSV entry
        for cif_file in blob_dir.glob("*.cif"):
            name = cif_file.stem
            if name not in scores:
                scores[name] = 0.0

        if not scores:
            logger.warning(f"No conformers found in {blob_dir}")
            continue

        # Re-write CSV sorted by score descending
        csv_data = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["conformer_name", "consistency_iou"])
            writer.writerows(csv_data)
        logger.info(f"Created CSV table: {csv_file} with {len(csv_data)} entries")

        # Copy best CIF to the 'best' directory
        best_name, best_score = csv_data[0]
        best_cif = blob_dir / f"{best_name}.cif"
        if best_cif.exists():
            dest = best_dir / f"{blob_dir.name}_{best_name}.cif"
            try:
                shutil.copy2(best_cif, dest)
                logger.info(f"Copied best result: {dest} (score: {best_score:.4f})")
            except OSError as e:
                logger.warning(f"Failed to copy {best_cif} to best directory: {e}")
        else:
            logger.warning(f"Best .cif file not found: {best_cif}")


def load_config(
    gpu: int = 0,
    detection_batch_size: int | None = None,
    contour_level: float | None = None,
) -> object:
    """Load Emap2lig configuration using Hydra.

    Args:
        gpu: CUDA GPU device ID.
        detection_batch_size: Override detection batch size from config.
        contour_level: Override contour level from config.

    Returns:
        Hydra configuration object.
    """
    overrides = []
    if gpu is not None:
        overrides.append(f"gpu={gpu}")
    if detection_batch_size is not None:
        overrides.append(f"detection_batch_size={detection_batch_size}")
    if contour_level is not None:
        overrides.append(f"contour_level={contour_level}")
    config_dir = Path(__file__).resolve().parent
    with initialize_config_dir(version_base=None, config_dir=str(config_dir)):
        cfg = compose(config_name="emap2lig", overrides=overrides)
    return cfg


def run_structure_modeling(
    blobs_dir: Path | str,
    output_dir: Path | str,
    ligand_records: list[LigandRecord],
    cfg,
    gpu: int = 0,
    multiplicity: int = 1,
    blob_ids: list[int] | None = None,
) -> int:
    """Run structure modeling on detected blobs (Stage 2).

    Takes pre-detected blobs from Stage 1 and a list of ligand records,
    then runs the diffusion-based structure modeling pipeline.

    Args:
        blobs_dir: Directory containing detected blob NPZ files from Stage 1.
        output_dir: Root output directory (will contain ``build_struct/`` subdirectory).
        ligand_records: List of :class:`LigandRecord` objects specifying ligands.
        cfg: Hydra configuration object (from :func:`load_config`).
        gpu: CUDA GPU device ID.
        multiplicity: Number of conformers per blob per ligand.
        blob_ids: If provided, only process blobs with these IDs.
            When ``None`` (default), all blobs in *blobs_dir* are processed.

    Returns:
        Status code: 0 for success, 1 for failure.
    """
    blobs_dir = Path(blobs_dir)
    output_dir = Path(output_dir)
    build_struct_dir = output_dir / "build_struct"
    build_struct_dir.mkdir(parents=True, exist_ok=True)

    # Enforce GPU-only inference.
    _require_cuda_gpu(gpu)

    logger.info("Starting ligand dataset preparation.")

    # Load blob paths, optionally filtered to specific blob IDs
    blob_paths = sorted(list(blobs_dir.glob("blob_*.npz")))
    if blob_ids is not None:
        allowed = set(blob_ids)
        blob_paths = [p for p in blob_paths if int(p.stem.split("_")[1]) in allowed]
        logger.info(f"Filtered to {len(blob_paths)} blobs (ids={blob_ids})")
    if not blob_paths:
        logger.error("No blob files found. Exiting.")
        return 1

    logger.info(f"Processing {len(ligand_records)} ligand records")

    # For incremental runs (specific blob_ids), use an isolated ligands
    # directory so the dataset only sees the newly requested ligands.
    incremental_ligands_dir: Path | None = None
    if blob_ids is not None:
        incremental_ligands_dir = (
            output_dir / "preprocess" / f"_ligands_{uuid.uuid4().hex[:8]}"
        )

    _, ligands_object_dir = prepare_ligand_dataset(
        ligand_records=ligand_records,
        output_dir=output_dir,
        ligands_dir=incremental_ligands_dir,
    )

    ligand_paths = sorted(list(Path(ligands_object_dir).glob("*.npz")))
    if not ligand_paths:
        logger.error("No ligand files found. Exiting.")
        return 1

    logger.info("Ligand dataset preparation completed.")

    logger.info("Starting inference with PyTorch Lightning.")

    # Use the already-filtered blob_paths as density inputs
    density_blob_paths = blob_paths
    if not density_blob_paths:
        logger.error("No density blob files found. Exiting.")
        return 1

    # Create dataset with CLI-specified multiplicity
    dataset = LigandModelingDataset(
        density_object_list=density_blob_paths,
        ref_mol_dir=ligands_object_dir,
        multiplicity=multiplicity,
    )

    # Create dataloader — structure modeling always uses batch_size=1
    # (one blob-ligand pair at a time; multiplicity controls conformer count)
    dataloader = DataLoader(
        dataset,
        batch_size=1,
        shuffle=False,
        num_workers=cfg.num_workers,
        collate_fn=collate_fn,
    )

    # Initialize model
    logger.info(f"Instantiating model {cfg.model._target_}")
    model = instantiate(cfg.model)

    # Set multiplicity from CLI argument (no need for model to infer it)
    model.predict_args.multiplicity = multiplicity

    # Create writer callback
    writer = LigandWriter(
        output_dir=build_struct_dir,
        output_format="mmcif",
    )

    # Configure trainer
    trainer_kwargs = {
        "accelerator": "gpu",
        "devices": [gpu],
        "callbacks": [writer],
        "logger": False,  # Disable default logger
    }

    # Create trainer
    logger.info("Initializing PyTorch Lightning Trainer")
    trainer = Trainer(**trainer_kwargs)

    # Run prediction using dataloader directly
    logger.info(f"Running inference on {len(dataset)} combinations")
    trainer.predict(model, dataloaders=dataloader)

    logger.info("Inference completed.")

    # Clean up temporary ligands directory used for incremental runs
    if incremental_ligands_dir is not None and incremental_ligands_dir.exists():
        shutil.rmtree(incremental_ligands_dir, ignore_errors=True)
        logger.info(f"Cleaned up temporary ligands dir: {incremental_ligands_dir}")

    # Create CSV tables for each blob
    create_blob_csv_tables(build_struct_dir)

    return 0


app = typer.Typer()


@app.command()
def main(
    input_map: str = typer.Option(
        ..., "--input-map", help="Path to input cryo-EM map file"
    ),
    output_dir: str = typer.Option(
        "./output", "--output-dir", help="Directory to save output files"
    ),
    gpu: int = typer.Option(0, "--gpu", help="CUDA GPU device ID"),
    detection_batch_size: int | None = typer.Option(
        None,
        "--detection-batch-size",
        help="Batch size for detection model sliding window inference (overrides config default of 16)",
    ),
    emdb_id: str | None = typer.Option(None, "--emdb-id", help="EMDB ID for the map"),
    contour_level: float | None = typer.Option(
        None, "--contour-level", help="Contour level for the map"
    ),
    ligand_list: str | None = typer.Option(
        None, "--ligand-list", help="Path to ligand list file"
    ),
    multiplicity: int = typer.Option(
        1, "--multiplicity", help="Number of conformers per blob per ligand"
    ),
    seed: int = typer.Option(42, "--seed", help="Random seed"),
):
    """Detect ligands in cryo-EM density maps using Emap2lig."""
    # Enforce GPU-only inference before loading config.
    try:
        _require_cuda_gpu(gpu)
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc), param_hint="--gpu") from exc

    # Set random seed
    seed_everything(seed)

    # Load configuration
    cfg = load_config(
        gpu=gpu, detection_batch_size=detection_batch_size, contour_level=contour_level
    )

    # Create output directories
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Stage 1: Detect ligand blobs
    status, blobs_dir = detect_ligand_objects(input_map, output_path, cfg, emdb_id)

    # If detection failed, exit
    if status != 0:
        logger.error("Ligand object detection failed. Exiting.")
        return status

    # Check if ligand list is provided
    if ligand_list is None:
        logger.error("Ligand list not provided. Exiting.")
        return 1

    # Parse ligand list (supports both simple and YAML formats)
    ligand_records = parse_ligand_list(Path(ligand_list))

    # Stage 2: Run structure modeling
    return run_structure_modeling(
        blobs_dir=blobs_dir,
        output_dir=output_path,
        ligand_records=ligand_records,
        cfg=cfg,
        gpu=gpu,
        multiplicity=multiplicity,
    )


if __name__ == "__main__":
    app()
