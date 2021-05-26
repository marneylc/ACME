# builtin imports
import gc
import pickle
from typing import Iterable
from typing import List
import sqlite3

# third party lib imports
from src.nltk_tools import *
from jsonpickle import encode as jp_encode, decode as jp_decode

# project specific custom code imports
from src.pathing_defs import *
from src.custom_logger import get_logger,get_logging_file_target,DEBUGGING

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


def to_list(obj)->List[str]:
    if isinstance(obj,list):
        return obj
    if isinstance(obj,bytes):
        obj = obj.decode("utf-8")
    if isinstance(obj,str):
        return [s.strip() for s in obj.split(",")]
    if isinstance(obj,Iterable):
        return list(obj)
