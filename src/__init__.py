import gc
import pickle
from src.nltk_tools import *
from src.pathing_defs import *
from src.custom_logger import get_logger,get_logging_file_target
from typing import List


src_warning_logger = get_logger(__name__,"warnings",level="WARNING")

def handle_warning_about_unexpected_exceptions(be:BaseException,*details:List):
    src_warning_logger.warning(f"{type(be)}:"
                               f"\n\t\t{be.args}"
                               f"\n\t\t{details}")


def un_pickle(fd_or_data, is_file:bool=True):
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


def do_pickle(obj,fd=None):
    if gc.isenabled():
        gc.disable()
    try:
        if fd is None:
            return pickle.dumps(obj,protocol=-1)
        return pickle.dump(obj,fd,protocol=-1)
    except BaseException as be:
        handle_warning_about_unexpected_exceptions(be,"")
    finally:
        if not gc.isenabled():
            gc.enable()






