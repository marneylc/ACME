from pathlib import Path


project_root_folder = Path(__file__).resolve().parent.parent
cache_folder = project_root_folder.joinpath("cache_files")
root_dodo = project_root_folder.joinpath("dodo.py")