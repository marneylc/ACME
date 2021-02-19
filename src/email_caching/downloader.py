import imaplib
import warnings
import pickle
import gc
from pathlib import Path
import hashlib
from email.parser import BytesParser
from email.policy import default as policy_default
from src.custom_logger import get_logger
import re

body_structure_splitter = re.compile("\)\(")
info = get_logger(__name__,"downloader status updates",level="INFO")

warnings.filterwarnings("ignore")


def pickle_load(path,mode="rb", default=None):
    if not mode.endswith("b"):
        mode += "b"
    if isinstance(path,str):
        path = Path(path).resolve()
    if path.exists():
        with open(path, mode) as f:
            gc.disable()
            try:
                return pickle.load(f)
            finally:
                gc.enable()
    else:
        if default is None:
            default = {}
        return default


def pickle_dump(obj,path,mode="wb",/, protocol=-1):
    if not mode.endswith("b"):
        mode += "b"
    if isinstance(path,Path):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.with_suffix(".pkl")
    with open(path, mode) as f:
        gc.disable()
        try:
            pickle.dump(obj,f,protocol=protocol)
        finally:
            gc.enable()


def email_downloader(cache_root=None)->None:
    """Given a list of output directory paths, will download files from our email address and cache them.

    :param targets: A list of strings representing directory paths (absolute or relative) for where we should
                    cache our downloaded emails.
    :return: None
    """
    if cache_root is None:
        from src import cache_folder
        cache_root = str(cache_folder.joinpath("cached_emails.pkl"))
    if not isinstance(cache_root,Path):
        cache_location = Path(cache_root).resolve()
    else:
        cache_location = cache_root
    header_keys = {}
    existing_data = pickle_load(cache_location)
    header_keys.update(existing_data)
    target_email = "luke.email.ryan.here@gmail.com"
    bad_practice = "oferoyrtvimlhqdd"
    imap_url = "imap.gmail.com"
    emails_dir = cache_location.parent.joinpath("emails")
    emails_dir.mkdir(exist_ok=True)
    bytes_parser = BytesParser(policy=policy_default)
    with imaplib.IMAP4_SSL(imap_url) as con:
        con.login(target_email,bad_practice)
        con.select("INBOX") # defaults to selecting "INBOX"
        inbox_status = con.status('INBOX','(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)')
        info.info(f"{inbox_status=}")
        # con.search(None,"ALL") returns a tuple, with the first element being the condition of the data_ids.
        _,data_ids = con.search(None,"ALL")
        # data = con.search(None,"FROM","petersryan84@gmail.com")[1]
        mails = [elem for d in data_ids for elem in d.split()]
        # full_retrieval_code = "(RFC822)"
        message_retrieval_code = "(RFC822.TEXT)"
        header_retrieval_code = "(RFC822.HEADER)"
        structure_retrieval_code = "(BODY)" # gets structural details about the message body (data encodings and such)
        u8 = "UTF-8"
        for mail_id in mails:
            # em_condition: email query condition
            # em_data: the data retrieval code
            _,header_data = con.fetch(mail_id,header_retrieval_code)
            email_header = bytes_parser.parsebytes(header_data[0][1],headersonly=True)
            header_key = "|".join([email_header["To"],
                                   email_header["From"],
                                   email_header["Subject"],
                                   email_header["Received"]])
            if header_key not in header_keys:
                _,((_,message,*_),*_) = con.fetch(mail_id,message_retrieval_code)
                _,body_structure = con.fetch(mail_id, structure_retrieval_code)
                body_structure = [body_structure_splitter.sub(")|(",b.decode(u8)).split("|") for b in body_structure]
                email_msg = bytes_parser.parsebytes(message)

                file_hash = hashlib.sha224(str(header_key).encode(u8))
                fname = emails_dir.joinpath(file_hash.hexdigest())
                pickle_dump((email_header,body_structure,email_msg),fname)
                header_keys[header_key] = fname
    pickle_dump(header_keys,cache_location)

def doit_email_downloader(targets:list):
    email_downloader(targets[0])

if __name__ == '__main__':
    my_imaginary_path = "../another_dir/header_keys.pkl"
    test_cache_target = Path(my_imaginary_path).resolve()
    # here = Path(__file__).resolve().parent
    # test_cache_target = here.joinpath("test_cache_dir/header_keys.pkl")
    test_cache_target.parent.mkdir(parents=True,exist_ok=True)
    email_downloader(test_cache_target)
