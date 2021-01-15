from src.email_caching.downloader import email_downloader
from src.keyword_extraction.extraction_functions import extract_root_messages,extract_keywords
from src.keyword_extraction.extraction_functions import message_roots_cache_dir, message_roots_map_fname
from src.keyword_extraction.extraction_functions import output_target_files
from src import cache_folder
import gc, pickle


def depickle(fd):
    gc.disable()
    try:
        return pickle.load(fd)
    finally:
        gc.enable()


def task_download_emails():
    actions = [email_downloader]
    targets = [str(cache_folder.joinpath("cached_emails.pkl"))]
    return dict(actions=actions,targets=targets,verbosity=2)


def task_extract_root_message():
    actions = [extract_root_messages]
    targets = [str(cache_folder.joinpath(fname)) for fname in message_roots_cache_dir]
    with open(str(cache_folder.joinpath("cached_emails.pkl")),"rb") as f:
        cached_files = depickle(f)
    file_dep = [v for v in cached_files.values()]
    return dict(actions=actions,file_dep=file_dep,targets=targets,verbosity=2)


def task_extract_keywords():
    actions = [extract_keywords]
    cached_emails_map_path = cache_folder.joinpath(message_roots_cache_dir[0]).joinpath(message_roots_map_fname)
    with open(cached_emails_map_path,"rb") as f:
        extracted_roots_map = depickle(f)
    file_dep = [str(cached_emails_map_path)]
    [file_dep.append(str(v)) for v in extracted_roots_map.values()]
    targets = [str(cache_folder.joinpath(output_target_files.keywords))]
    return dict(actions=actions,file_dep=file_dep,targets=targets,verbosity=2)


def emulate_doit(doit_d:dict):
    actions = doit_d.pop("actions")
    verbosity = doit_d.pop("verbosity",None)
    for func_a in actions:
        func_a(**doit_d)


if __name__ == '__main__':
    # import os
    # os.system("doit")
    tasks = []
    # tasks.append(task_download_emails)
    # tasks.append(task_extract_root_message)
    tasks.append(task_extract_keywords)
    for task in tasks:
        emulate_doit(task())