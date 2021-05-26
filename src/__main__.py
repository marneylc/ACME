# builtin imports
import subprocess
import os
import sqlite3 as sqlt3
import json

# third party imports
from scipy.sparse.csr import csr_matrix
# import graphviz

# custom code imports
from src import *
from src.email_caching.cache_class_defs import EmailItem
from src.lemma_extraction.word_extraction_classes import SentenceWordTagger, MessageBodyTagging, LemmaExtractor


#######################################################################################################################
# sqlite3 adapter definitions and their registration
#######################################################################################################################
def adapt_complex_json(obj):
    if gc.isenabled():
        gc.disable()
    try:
        return jp_encode(obj,indent=4)
    finally:
        if not gc.isenabled():
            gc.enable()

def adapt_simple_json(obj):
    if gc.isenabled():
        gc.disable()
    try:
        return json.dumps(obj,indent=4)
    finally:
        if not gc.isenabled():
            gc.enable()


sqlt3.register_adapter(list,adapt_simple_json)
sqlt3.register_adapter(tuple,adapt_simple_json)
sqlt3.register_adapter(dict,adapt_complex_json)
sqlt3.register_adapter(csr_matrix,adapt_complex_json)


#######################################################################################################################
# sqlite3 converter definitions and their registration
#######################################################################################################################
def convert_special_json(obj):
    if gc.isenabled():
        gc.disable()
    try:
        return jp_decode(obj.decode("utf-8"), safe=True, classes=[EmailItem, SentenceWordTagger, MessageBodyTagging, LemmaExtractor, dict, csr_matrix])
    finally:
        if not gc.isenabled():
            gc.enable()


def convert_simple_json(obj):
    if gc.isenabled():
        gc.disable()
    try:
        return json.loads(obj)
    finally:
        if not gc.isenabled():
            gc.enable()


sqlt3.register_converter(DB_SUPPORTED_TYPES["complex"], convert_special_json)
sqlt3.register_converter(DB_SUPPORTED_TYPES["simple"],convert_simple_json)


#######################################################################################################################
# project's primary console entry point
#######################################################################################################################

def main():
    # ToDo: configure arg parsing for CLI
    proj_base_info_logger.warning("EmailClassifier launched")
    old_cwd = os.getcwd()
    here = project_root_folder
    dodo_path,*_ = here.parent.rglob("**/dodo.py")
    if not dodo_path:
        dodo_path = here
    os.chdir(dodo_path)
    try:
        completed = subprocess.run(["doit"], shell=True, check=True, capture_output=True)
        completed.check_returncode()
        proj_base_info_logger.warning("EmailClassifier completed")
    except BaseException as be:
        proj_base_info_logger.warning("EmailClassifier terminated with an error")
        raise be
    finally:
        os.chdir(old_cwd)


def emulate_doit(doit_d:dict):
    actions = doit_d.pop("actions")
    verbosity = doit_d.pop("verbosity",None)
    for func_a in actions:
        func_a(**doit_d)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    do_doit = False
    if do_doit:
        main()
    else:
        from src.dodo import task_download_emails
        from src.dodo import task_extract_root_message
        from src.dodo import task_extract_lemma
        from src.dodo import task_consolidate_databases
        proj_base_info_logger.warning("EmailClassifier launched")
        tasks = []
        tasks.append(task_download_emails)
        tasks.append(task_extract_root_message)
        tasks.append(task_extract_lemma)
        tasks.append(task_consolidate_databases)

        for task in tasks:
            emulate_doit(task())
        proj_base_info_logger.warning("EmailClassifier completed")