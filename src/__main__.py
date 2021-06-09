from src.utils.__main__ import *


def emulate_doit(doit_d:dict):
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
        # tasks.append(task_download_emails)
        # tasks.append(task_extract_root_message)
        # tasks.append(task_extract_lemma)
        # tasks.append(task_consolidate_databases)
        tasks.append(task_generate_db_erd)

        for task in tasks:
            emulate_doit(task())
        proj_base_info_logger.warning("EmailClassifier completed")