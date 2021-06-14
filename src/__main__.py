"""
@src.__main__.py
The primary entry point for the project.
"""
from utils.__main__ import *
##
# A debugging function that allows us to adhere to the signature requirements defined by Doit (a third party library)
# but without having to handle the technical details of launching multiple child terminals via the subprocess module.
#
# This is just to simplify debugging of internal code before integrating Doit to automate task execution.
def emulate_doit(doit_d:dict):
    """
    A debugging function that allows us to adhere to the signature requirements defined by Doit (a third party library)
    but without having to handle the technical details of launching multiple child terminals via the subprocess module.

    This is just to simplify debugging of internal code before integrating Doit to automate task execution.
    :param doit_d: A dictionary that should contain the following key/value pair structure:
                {
                    'actions': types.FunctionType, # target function that should be executed with arguments [file_dep, targets]
                    'targets': List[str], # a list of path-strings for target output files, if any, else an empty list
                    'file_dep': list[str], # a list of path-strings for input/dependency files, if any, else an empty list.
                }
    :type doit_d: dict
    :return:
    :rtype:
    """
    actions = doit_d.pop("actions")
    verbosity = doit_d.pop("verbosity",None)
    for func_a in actions:
        func_a(**doit_d)


if __name__ == '__main__':
    import logging
    if DEBUGGING:
        logging.basicConfig(level=logging.DEBUG)
    do_doit = False
    if do_doit:
        main()
    else:
        from src.dodo import task_download_emails
        from src.dodo import task_extract_root_message
        from src.dodo import task_extract_lemma
        from src.dodo import task_consolidate_databases
        from src.dodo import task_generate_db_erd
        proj_base_info_logger.warning("EmailClassifier launched")
        tasks = []
        tasks.append(task_download_emails)
        tasks.append(task_extract_root_message)
        tasks.append(task_extract_lemma)
        tasks.append(task_consolidate_databases)
        tasks.append(task_generate_db_erd)
        for task in tasks:
            emulate_doit(task())
        proj_base_info_logger.warning("EmailClassifier completed")