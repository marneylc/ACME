import subprocess
import os
# import pathlib as pl
from pathlib import Path
import argparse


def console_arg_parse():
    parser = argparse.ArgumentParser("email_classifier")
    # ToDo: Define console arguments
    return parser.parse_args()

def main():
    here = Path(__file__).resolve().parent
    old_cwd = os.getcwd()
    os.chdir(here)
    try:
        subprocess.run(["doit"], shell=True, check=True, capture_output=True)
    finally:
        os.chdir(old_cwd)

# if __name__ == '__main__':
#     exec_d = task_init_configs()
#     func = exec_d.pop("actions")[0](**exec_d)