from pathlib import Path
from src.email_caching.downloader import doit_email_downloader
from src.lemma_extraction.extraction_functions import extract_lemma
from src.body_extraction.extraction_functions import extract_root_messages
from src.db_tools.database_consolidation import doit_consolidate_databases
from src.db_tools.database_consolidation import doit_generate_erd
# from src.lemma_extraction import output_target_files
from src.utils.pathing_defs import cache_folder
from src import DB_PATH_DICT


# extraction_targets = []


def load_analysis_tools_helper(*args):
    print(f"load_analysis_tools_helper({args=})")

    return args

def confirm_package_setup():
    def inner(targets:list, file_dep:list):
        pass
    actions = [inner]
    egg_root = Path(__file__).parent.relative_to("EmailClassification/EmailClassification.egg-info").resolve()
    targets = [str(egg_root)]

def task_download_emails():
    actions = [doit_email_downloader]
    targets = [str(cache_folder.joinpath("cached_emails.pkl"))]
    return dict(actions=actions,targets=targets,verbosity=2)

def task_extract_root_message():
    actions = [extract_root_messages]
    targets = [str(DB_PATH_DICT["body"])]
    file_dep = [str(cache_folder.joinpath("ntlk_packages")), str(DB_PATH_DICT["email"])]
    return dict(actions=actions,file_dep=file_dep,targets=targets,verbosity=2)

def task_extract_lemma():
    # global extraction_targets
    actions = [extract_lemma]
    # cached_emails_map_path = cache_folder.joinpath(message_roots_cache_dir[0]).joinpath(message_roots_map_fname)
    # with open(cached_emails_map_path,"rb") as f:
    #     extracted_roots_map = undo_pickle(f)
    # file_dep = [str(cached_emails_map_path)]
    # [file_dep.append(str(v)) for v in extracted_roots_map.values()]
    file_dep = [str(DB_PATH_DICT["body"]), str(DB_PATH_DICT["email"])]
    # targets = [str(cache_folder.joinpath(output_target_files.keywords))]
    targets = [str(DB_PATH_DICT["lemma"])]
    # extraction_targets = targets[:]
    return dict(actions=actions,file_dep=file_dep,targets=targets,verbosity=2)

def task_consolidate_databases():
    actions=[doit_consolidate_databases]
    file_dep = list(map(str,(DB_PATH_DICT[k] for k in ("email","body","lemma"))))
    targets = [str(DB_PATH_DICT["consolidated"])]
    return dict(actions=actions,file_dep=file_dep,targets=targets,verbosity=2)

def task_generate_db_erd():
    actions=[doit_generate_erd]
    output_target = cache_folder.joinpath("db_diagrams")
    output_target.mkdir(parents=True,exist_ok=True)
    file_dep = [output_target.joinpath(name) for name in output_target.iterdir() if name.suffix==".er"]
    # targets = [str(output_target.joinpath("central_db.png")), str(output_target.joinpath("central_db.er"))]
    targets = [str(p.with_name(p.stem+".png")) for p in file_dep]
    file_dep = [str(p) for p in file_dep]
    # file_dep = [str(DB_PATH_DICT["consolidated"])]
    # file_dep = list(map(str,(DB_PATH_DICT[k] for k in ("email","body","lemma"))))
    # targets = [str(DB_PATH_DICT["consolidated"])]
    return dict(actions=actions,file_dep=file_dep,targets=targets,verbosity=2)

# def task_load_analysis_tools():
#     return dict(actions=load_analysis_tools_helper , targets=["load_analysis_tools_dummy_file.txt"])


# def task_categorize_emails():
#     return dict(actions=lambda *args:args, file_dep=["load_analysis_tools_dummy_file.txt"], targets=["categorize_emails_dummy_file.txt"])
