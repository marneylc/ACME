from pathlib import Path
from src.email_caching.downloader import doit_email_downloader
from src.lemma_extraction.extraction_functions import extract_root_messages,extract_lemma
from src.lemma_extraction.extraction_functions import message_roots_cache_dir, message_roots_map_fname
from src.db_tools.database_consolidation import doit_consolidate_databases
# from src.lemma_extraction import output_target_files
from src.pathing_defs import cache_folder
from src.__main__ import main
from src import do_pickle, undo_pickle, DB_PATH_DICT


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
    pass

# def task_load_analysis_tools():
#     return dict(actions=load_analysis_tools_helper , targets=["load_analysis_tools_dummy_file.txt"])


# def task_categorize_emails():
#     return dict(actions=lambda *args:args, file_dep=["load_analysis_tools_dummy_file.txt"], targets=["categorize_emails_dummy_file.txt"])
