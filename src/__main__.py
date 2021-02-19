import subprocess
import os
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    old_cwd = os.getcwd()
    os.chdir(here)
    try:
        subprocess.run(["doit"], shell=True, check=True, capture_output=True)
    finally:
        os.chdir(old_cwd)


if __name__ == '__main__':
    main()
