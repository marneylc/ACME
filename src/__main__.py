import subprocess
import os
from pathlib import Path


def main():
    old_cwd = os.getcwd()
    here = Path(__file__).resolve().parent
    dodo_path = list(here.parent.glob("**/dodo.py"))
    if dodo_path:
        dodo_path = dodo_path[0]
    else:
        dodo_path = here
    os.chdir(here)
    try:
        subprocess.run(["doit"], shell=True, check=True, capture_output=True)
    finally:
        os.chdir(old_cwd)


def emulate_doit(doit_d:dict):
    actions = doit_d.pop("actions")
    verbosity = doit_d.pop("verbosity",None)
    for func_a in actions:
        func_a(**doit_d)

if __name__ == '__main__':
    do_doit = False
    if do_doit:
        main()
    else:
        from src.dodo import task_download_emails,task_extract_root_message,task_extract_keywords
        tasks = []
        # tasks.append(task_download_emails)
        tasks.append(task_extract_root_message)
        tasks.append(task_extract_keywords)

        for task in tasks:
            emulate_doit(task())