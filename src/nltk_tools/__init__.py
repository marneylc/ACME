from src.custom_logger import import_warnings_logger
from src.pathing_defs import cache_folder

try:
    import nltk
    from nltk.downloader import _downloader as nltk_loader
    nltk_packages = cache_folder.joinpath("nltk_packages")

    if not nltk_packages.exists():
        nltk_packages.mkdir(parents=True,exist_ok=True)
        nltk.data.path.append(str(nltk_packages))
        nltk_loader.download("all", download_dir=str(nltk_packages),quiet=True)
        print(nltk.data.path)
        nltk.downloader.Downloader().list(str(nltk_packages))
    else:
        nltk.data.path.append(str(nltk_packages))
except ImportError:
    import_warnings_logger.warning(f"The NLTK library isn't available on this machine, no NLP tools will be enabled.",exc_info=True)