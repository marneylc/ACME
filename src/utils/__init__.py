# builtin imports
import gc
import pickle
from typing import Iterable
from typing import List
import sqlite3
from textwrap import fill

# third party lib imports
from jsonpickle import encode as jp_encode, decode as jp_decode

# project specific custom code imports
from .pathing_defs import *
from .custom_logger import get_logger,get_logging_file_target,DEBUGGING
from .custom_logger import import_warnings_logger
from .pathing_defs import cache_folder


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
plain_info_logger = get_logger("EmailClassifier",__name__+": plain logger",level="INFO")
("\n".join(txt))

proj_base_info_logger = get_logger("EmailClassifier",__name__+": root logger",level="INFO")

def alias_keys(d:dict):
    keys = tuple(d.keys())
    for k in keys:
        val = d[k]
        if isinstance(k,str):
            new_k = k.split("_")[0]
            d.setdefault(new_k,val)
            d.setdefault(new_k.lower(), val)


# defining global references to the data types our database objects can support.
DB_INTEGER = "INTEGER"
DB_NULL = "NULL"
DB_REAL = "REAL"
DB_TEXT = "TEXT"
DB_BLOB = "BLOB"
PROJ_CUSTOM_CLASSES = "COMPLEX_JSON"
PROJ_SIMPLE_JSON = "SIMPLE_JSON"

# project scoped dictionaries
DB_SUPPORTED_TYPES = {
    "int":DB_INTEGER,
    "integer":DB_INTEGER,
    int:DB_INTEGER,
    "None":DB_NULL,
    "NULL":DB_NULL,
    None:DB_NULL,
    "float":DB_REAL,
    "REAL":DB_REAL,
    float:DB_REAL,
    "str":DB_TEXT,
    "TEXT":DB_TEXT,
    str:DB_TEXT,
    "bytes":DB_BLOB,
    "BLOB":DB_BLOB,
    bytes:DB_BLOB,
    "custom_cls":PROJ_CUSTOM_CLASSES,
    PROJ_CUSTOM_CLASSES:PROJ_CUSTOM_CLASSES,
    PROJ_CUSTOM_CLASSES.lower():PROJ_CUSTOM_CLASSES,
    PROJ_SIMPLE_JSON:PROJ_SIMPLE_JSON,
    PROJ_SIMPLE_JSON.lower():PROJ_SIMPLE_JSON,
}
alias_keys(DB_SUPPORTED_TYPES)

DB_PATH_DICT = {
    "email_cache":cache_folder.joinpath("sql3_email.db"),
    "body_cache":cache_folder.joinpath("sql3_message_body.db"),
    "lemma_cache":cache_folder.joinpath("sql3_extracted_lemma.db"),
    "consolidated_cache":cache_folder.joinpath("sql3_consolidated.db")
}
alias_keys(DB_PATH_DICT)

TABLE_NAMES = {
    "email_cache":["emails"],
    "body_cache":["message_body"],
    "lemma_cache":["all_lemma", "no_stopwords_lemma"],
}
alias_keys(TABLE_NAMES)

src_warning_logger = get_logger("EmailClassifier",__name__+": warning",level="WARNING")


def handle_warning_about_unexpected_exceptions(be:BaseException,*details:Iterable):
    src_warning_logger.warning(f"{type(be)}:"
                               f"\n\t\t{be.args}"
                               f"\n\t\t{details}")


def undo_pickle(fd_or_data, is_file:bool=True):
    if gc.isenabled():
        gc.disable()
    try:
        if is_file:
            return pickle.load(fd_or_data)
        return pickle.loads(fd_or_data)
    except BaseException as be:
        handle_warning_about_unexpected_exceptions(be,"")
    finally:
        if not gc.isenabled():
            gc.enable()


def do_pickle(obj,fd=None,protocol=-1):
    if gc.isenabled():
        gc.disable()
    try:
        if fd is None:
            return pickle.dumps(obj,protocol=protocol)
        return pickle.dump(obj,fd,protocol=protocol)
    except BaseException as be:
        handle_warning_about_unexpected_exceptions(be,"")
    finally:
        if not gc.isenabled():
            gc.enable()


class JPickleSerializable:
    _my_attrs:List[str]

    def __init__(self, *class_attrs:List[str]):
        self._my_attrs = class_attrs

    def to_json(self, indent:int=4):
        try:
            if gc.isenabled():
                gc.disable()
            return jp_encode(self, indent=indent)
        finally:
            if not gc.isenabled():
                gc.enable()

    def __conform__(self,protocol):
        if protocol is sqlite3.PrepareProtocol:
            return self.to_json()


class TaggerBase(JPickleSerializable):
    @staticmethod
    def word_token_cleanup(tokens):
        for i in range(len(tokens) - 1, 0, -1):
            if "'" in tokens[i]:
                tokens[i - 1] += tokens.pop(i).replace("'", "_^_")
        return " ".join(tokens)

def to_list(obj)->List[str]:
    if isinstance(obj,list):
        return obj
    if isinstance(obj,bytes):
        obj = obj.decode("utf-8")
    if isinstance(obj,str):
        return [s.strip() for s in obj.split(",")]
    if isinstance(obj,Iterable):
        return list(obj)
