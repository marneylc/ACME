from pathlib import Path
from src.custom_logger import import_warnings_logger
from src.pathing_defs import cache_folder
from textwrap import fill


nltk_packages = Path(cache_folder.root).resolve().absolute().joinpath("nltk_packages")
nltk_path_str = str(nltk_packages)
try:
    import nltk
    from nltk.downloader import _downloader as nltk_loader
    if not (nltk_packages.exists() and any(nltk_packages.iterdir())):
        nltk_packages.mkdir(parents=True,exist_ok=True)
        nltk.data.path.insert(0,nltk_path_str)
        nltk.download(download_dir=nltk_path_str)
        # nltk_loader.download("all", download_dir=str(nltk_packages),quiet=True)
        # nltk_loader.download("wordnet",download_dir=nltk_path_str,quiet=True)
        # nltk_loader.download("words",download_dir=nltk_path_str,quiet=True)
        import_warnings_logger(f"created the nltk package folder at: \n\t{nltk.data.path}")
    else:
        nltk.data.path.append(str(nltk_packages))
except ImportError:
    nltk = None
    nltk_loader = None
    import_warnings_logger(f"The NLTK library isn't available on this machine, no NLP tools will be enabled.",exc_info=True)


class PoliteDownloader(nltk.downloader.Downloader):
    """
    Subclassed the Downloader provided by nltk to give better control over the garbage console output the
    default implementation forced on us.
    """
    ESC_SEQ = "\033["
    charc = 90  # charcoal
    purp = 35  # purple
    green = 32  # green -- might be just my eyes, but green(32) and yellow(33) look almost identical
    dull_cyan = 36  # dull-cyan
    bright_purp = 95  # bright-purple
    bright_red = 91  # bright-red
    COLOR_RESET = ESC_SEQ + "0m"
    formatted_green = f"{ESC_SEQ}1;{green}m"
    formatted_cyan = f"{ESC_SEQ}1;{dull_cyan}m"
    formatted_charc = f"{ESC_SEQ}1;{charc}m"
    formatted_red = f"{ESC_SEQ}1;{bright_red}m"
    def list(self, download_dir=None, show_packages=True, show_collections=True, header=True,
             skip_installed=False, max_line_width:int=120, color_coded:bool=False, skip_not_installed:bool=True):
        txt = []
        if download_dir is None:
            download_dir = self._download_dir
            txt.append("Using default data directory (%s)" % download_dir)
        if header:
            breaker = "=" * (26 + len(self._url))
            txt.append(breaker)
            txt.append(" Data server index for <%s>" % self._url)
            txt.append(breaker)
        stale = partial = False
        if color_coded:
            prefix_states = {
                        self.INSTALLED: f"{self.formatted_green}[*]{self.COLOR_RESET}",
                        self.STALE: f"{self.formatted_charc}[-]{self.COLOR_RESET}",#"[-]",
                        self.PARTIAL: f"{self.formatted_cyan}[P]{self.COLOR_RESET}",#"[P]",
                        self.NOT_INSTALLED: f"{self.formatted_red}[ ]{self.COLOR_RESET}",#"[ ]",
                    }
        else:
            prefix_states = {
                        self.INSTALLED: "[*]",
                        self.STALE: "[-]",
                        self.PARTIAL: "[P]",
                        self.NOT_INSTALLED: "[ ]",
                    }
        categories = []
        if show_packages:
            categories.append("packages")
        if show_collections:
            categories.append("collections")
        for category in categories:
            txt.append("%s:" % category.capitalize())
            for info in sorted(getattr(self, category)(), key=str):
                status = self.status(info, download_dir)
                if (status == self.INSTALLED and skip_installed) or (status == self.NOT_INSTALLED and skip_not_installed):
                    continue
                if status == self.STALE:
                    stale = True
                if status == self.PARTIAL:
                    partial = True
                prefix = prefix_states[status]
                name = fill(
                    "-" * 27 + (info.name or info.id), max_line_width, subsequent_indent=27 * " "
                )[27:]

                txt.append(f"  {prefix} {info.id.ljust(30,'.')} {name}")
            txt.append("")
        msg = f"({prefix_states[self.INSTALLED]} marks installed packages"
        if stale:
            msg += f"; {prefix_states[self.STALE]} marks out-of-date or corrupt packages"
        if partial:
            msg += f"; {prefix_states[self.PARTIAL]} marks partially installed collections"
        txt.append(fill(msg + ")", subsequent_indent=" ", width=max_line_width))
        return txt


txt = PoliteDownloader().list(nltk_path_str, color_coded=True, skip_not_installed=True)
txt.append("\n\n")
print("\n".join(txt))
