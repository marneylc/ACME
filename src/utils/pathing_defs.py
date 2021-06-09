from pathlib import Path

def get_proj_root():
    ret = Path(__file__).resolve()
    ref = ret
    while ref.name!="src":
        ref = ref.parent
        if not ref.name:
            break
    else:
        ret = ref
    return ret.parent

project_root_folder = get_proj_root()
cache_folder = project_root_folder.joinpath("cache_files")
root_dodo = project_root_folder.joinpath("dodo.py")