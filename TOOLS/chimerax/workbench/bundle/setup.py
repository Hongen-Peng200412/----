"""构建同注册名的中性工作台包; 科学适配器不打包, 部署配置由安装者显式给出."""

from setuptools import setup

setup(
    name="ChimeraX-LigandWorkbench",
    version="1.0.8",
    description="项目适配工作台与作者显示保存",
    author="Manuscript authors",
    url="https://www.rbvi.ucsf.edu/chimerax/",
    packages=["chimerax.ligand_workbench"],
    package_dir={"chimerax.ligand_workbench": "src"},
    package_data={"chimerax.ligand_workbench": ["docs/user/commands/*.html"]},
    python_requires=">=3.11",
    install_requires=["ChimeraX-Core~=1.0", "ChimeraX-UI~=1.0"],
    classifiers=["Framework :: ChimeraX", "ChimeraX :: Bundle :: General :: 1,1 :: chimerax.ligand_workbench ::  :: false", "ChimeraX :: Tool :: Ligand Workbench :: General :: 项目适配工作台", "ChimeraX :: Command :: ligwork :: General :: 项目适配工作台与作者显示保存"],
    zip_safe=False,
)
