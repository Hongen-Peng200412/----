"""构建纯 Python ChimeraX 工具 wheel; build、egg-info 与 wheel 输出由调用命令放入 temp 或正式留档."""

from setuptools import setup

setup(
    name="ChimeraX-LigandWorkbench",
    version="1.0.6",
    description="多配体交互画图与预算显示",
    author="Manuscript authors",
    url="https://www.rbvi.ucsf.edu/chimerax/",
    packages=["chimerax.ligand_workbench"],
    package_dir={"chimerax.ligand_workbench": "src"},
    package_data={"chimerax.ligand_workbench": ["docs/user/commands/*.html"]},
    python_requires=">=3.11",
    install_requires=["ChimeraX-Core~=1.0", "ChimeraX-UI~=1.0"],
    classifiers=[
        "Framework :: ChimeraX",
        "ChimeraX :: Bundle :: General :: 1,1 :: chimerax.ligand_workbench ::  :: false",
        "ChimeraX :: Tool :: Ligand Workbench :: General :: 多配体交互画图",
        "ChimeraX :: Command :: ligwork :: General :: 评估模式、预算、过滤与保存",
    ],
    zip_safe=False,
)
