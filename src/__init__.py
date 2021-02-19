from pathlib import Path
from src.custom_logger import get_logger

_init_warn_logger = get_logger(__name__,"import warnings",level="WARNING")

project_root_folder = Path(__file__).resolve().parent.parent
cache_folder = project_root_folder.joinpath("cache_files")
root_dodo = project_root_folder.joinpath("dodo.py")


try:
    import nltk
    from nltk.downloader import _downloader as nltk_loader
    nltk_packages = cache_folder.joinpath("nltk_packages")
    nltk_packages.mkdir(parents=True,exist_ok=True)
    nltk.data.path.append(str(nltk_packages))
    nltk_loader.download("all", download_dir=str(nltk_packages),quiet=True)
except ImportError:
    _init_warn_logger.warn(f"The NLTK library isn't available on this machine, no NLP tools will be enabled.",exc_info=True)


# print(nltk.data.path)
# nltk.downloader.Downloader().list(str(nltk_packages))



