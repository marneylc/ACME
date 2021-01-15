from pathlib import Path
import nltk
from nltk.downloader import _downloader as nltk_loader


project_root_folder = Path(__file__).resolve().parent.parent
cache_folder = project_root_folder.joinpath("cache_files")
root_dodo = project_root_folder.joinpath("dodo.py")
nltk_packages = cache_folder.joinpath("nltk_packages")
nltk_packages.mkdir(parents=True,exist_ok=True)
nltk.data.path.append(str(nltk_packages))
nltk_loader.download("all", download_dir=str(nltk_packages),quiet=True)
# print(nltk.data.path)
# nltk.downloader.Downloader().list(str(nltk_packages))



