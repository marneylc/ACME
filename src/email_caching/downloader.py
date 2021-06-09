# builtin imports
import sys
import imaplib
import warnings
import hashlib
import re
from pathlib import Path
from shutil import copytree
from email.parser import BytesParser
from email.policy import default as policy_default
from typing import List
import concurrent.futures as cf

# custom code imports
from src.utils.custom_logger import get_logger
from src.utils.pathing_defs import cache_folder
from src import do_pickle, undo_pickle, DB_PATH_DICT, TABLE_NAMES
from src.email_caching.cache_class_defs import EmailItem, EmailDB

body_structure_splitter = re.compile("\)\(")
info = get_logger("EmailClassifier",__name__+": downloader status updates",level="INFO")
err_log = get_logger("EmailClassifier",__name__+": downloader error messsage",level="ERROR")


# global references for strings mapping to imap content retrieval codes.
# full_retrieval_code = "(RFC822)"
message_retrieval_code = "(RFC822)"
header_retrieval_code = "(RFC822.HEADER)"
structure_retrieval_code = "(BODY)"  # gets structural details about the message body (data encodings and such)
U8 = "UTF-8"
nums_lst = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
id_to_str = lambda s:"_".join(nums_lst[i] for i in map(int,s))


def pickle_load(path,mode="rb", default=None):
    if not mode.endswith("b"):
        mode += "b"
    if isinstance(path,str):
        path = Path(path).resolve()
    if path.exists():
        with open(path, mode) as f:
            return undo_pickle(f)
    else:
        if default is None:
            default = {}
        return default


def pickle_dump(obj,path,mode="wb",/, protocol=-1):
    if not mode.endswith("b"):
        mode += "b"
    if isinstance(path,Path):
        path.parent.mkdir(parents=True,exist_ok=True)
        path = path.with_suffix(".pkl")
    with open(path, mode) as f:
        return do_pickle(obj,f,protocol)


def _threadable_logic(imap_url, target_email, bad_practice, mail_id, bytes_parser, existing_keys):
    label = id_to_str(str(mail_id)[2:].strip(" '"))
    email_item = None
    with imaplib.IMAP4_SSL(imap_url) as imap_con:
        imap_con.login(target_email, bad_practice)
        imap_con.select("INBOX")  # defaults to selecting "INBOX"
        # inbox_status = imap_con.status('INBOX', '(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)')
        # nonlocal imap_con, mem_db, db, existing_keys
        _, ((_, imap_header_bytes), *_) = imap_con.fetch(mail_id, header_retrieval_code)
        email_header = bytes_parser.parsebytes(imap_header_bytes, headersonly=True)
        msg_id = str(email_header["Message-ID"]).strip()
        if msg_id not in existing_keys:
            info.info(f"Adding to email db: {msg_id=}")
            _, body_structure = imap_con.fetch(mail_id, structure_retrieval_code)
            _, ((_, message, *_), *_) = imap_con.fetch(mail_id, message_retrieval_code)
            header_key = "|".join([email_header["To"],
                                   email_header["From"],
                                   email_header["Subject"],
                                   email_header["Received"]])
            hashed_header_key = hashlib.sha224(str(header_key).encode(U8))
            email_item = EmailItem(hashed_header_key,
                                   header_key,
                                   [body_structure_splitter.sub(")|(", b.decode(U8)).split("|") for b in body_structure],
                                   bytes_parser.parsebytes(message))
    return label, email_item


def email_downloader(cache_root=None)->None:
    """Given a path to the root directory for our output data cache, download files from our
    email address and cache them as a sqlite3 DB in that location.

    :param targets: A list of strings representing directory paths (absolute or relative) for where we should
                    cache our downloaded emails.
    :return: None
    """
    # warnings.filterwarnings("ignore")
    try:
        # ToDo: implement an argparse parser... >.< ...  to handle commandline interfacing.
        if cache_root is None:
            if len(sys.argv)>1:
                cache_root = cache_folder.joinpath(str(sys.argv[1]))
            else:
                cache_root = cache_folder.joinpath("cached_emails.pkl")
        if not isinstance(cache_root,Path):
            cache_location = Path(cache_root).resolve()
        else:
            cache_location = cache_root
        info.info(f"Caching emails to:\n\t{cache_location}")
        target_email = "luke.email.ryan.here@gmail.com"
        # ToDo: HIGH PRIORITY --
        #   Instead of saving the password inside the file, we should required the user to enter the password correctly
        #   within some limited number of attempts.
        bad_practice = "oferoyrtvimlhqdd"
        imap_url = "imap.gmail.com"
        # emails_dir = cache_location.parent.joinpath("emails")
        # emails_dir.mkdir(parents=True,exist_ok=True)
        bytes_parser = BytesParser(policy=policy_default)
        db_name = DB_PATH_DICT["email"]
        db_name.parent.mkdir(parents=True,exist_ok=True)
        email_table_name: List[str] = TABLE_NAMES["email"]
        db = EmailDB(db_name, email_table_name)
        with db("main"):
            main_curs, main_curs_pos = db.cursor
            existing_keys = set(v[0] for v in main_curs.execute(f"SELECT id FROM {email_table_name[0]};").fetchall())
            with imaplib.IMAP4_SSL(imap_url) as imap_con:
                imap_con.login(target_email, bad_practice)
                imap_con.select("INBOX")  # defaults to selecting "INBOX"
                inbox_status = imap_con.status('INBOX', '(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)')
                info.info(f"{inbox_status=}")
                # imap_con.search(None,"ALL") returns a tuple, with the first element being the condition of the data_ids.
                _, data_ids = imap_con.search(None, "ALL")
                # data = imap_con.search(None,"FROM","petersryan84@gmail.com")[1]
                mails = (elem for d in data_ids for elem in d.split())
            with cf.ThreadPoolExecutor() as tpe:
                ftrs = [tpe.submit(_threadable_logic, imap_url, target_email, bad_practice, mail_id, bytes_parser, existing_keys)
                        for mail_id in mails]
                for ftr in cf.as_completed(ftrs):
                    if not ftr.exception():
                        email_id,email_item = ftr.result()
                        if email_item is not None:
                            info.info(f"adding new row to db for email_id: {email_id}")
                            db.add_row(db.table_names[0],"main",email_item=email_item)
                db.commit()
    finally:
        pass
        # warnings.resetwarnings()


def doit_email_downloader(targets:list):
    target0 = Path(targets.pop(0)).resolve()
    email_downloader(target0)
    for target in targets[1:]:
        target = Path(target).resolve()
        copytree(target0,target)


if __name__ == '__main__':
    # my_imaginary_path = "../another_dir/header_keys.pkl"
    # test_cache_target = Path(my_imaginary_path).resolve()
    here = Path(__file__).resolve().parent
    test_cache_target = here.joinpath("test_cache_dir/header_keys.pkl")
    test_cache_target.parent.mkdir(parents=True,exist_ok=True)
    email_downloader(test_cache_target)
