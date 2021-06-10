from pathlib import Path

project_root_name = "EmailClassification"
project_root_folder = Path(__file__).resolve().parent
_tmp_root = Path(project_root_folder)
while _tmp_root.name and _tmp_root.name != project_root_name:
    _tmp_root = _tmp_root.parent
if _tmp_root.name == project_root_name:
    project_root_folder = _tmp_root
cache_folder = project_root_folder.joinpath("cache_files")
root_dodo = project_root_folder.joinpath("dodo.py")