import imaplib
import warnings
import pickle
import gc
from pathlib import Path
import hashlib
from io import BytesIO
from email.parser import BytesParser
from email.policy import default as policy_default
# import json


warnings.filterwarnings("ignore")


def shitty_id_gen():
    x = 0
    while True:
        yield x
        x += 1


def email_downloader(targets:list):
    cache_location = Path(targets[0]).resolve()
    header_keys = {}
    if cache_location.exists():
        with open(cache_location, "rb") as f:
            gc.disable()
            try:
                existing_data = pickle.load(f)
            finally:
                gc.enable()
        header_keys.update(existing_data)
    target_email = "luke.email.ryan.here@gmail.com"
    bad_practice = "oferoyrtvimlhqdd"
    imap_url = "imap.gmail.com"
    emails_dir = cache_location.parent.joinpath("emails")
    emails_dir.mkdir(exist_ok=True)
    bytes_parser = BytesParser(policy=policy_default)
    with imaplib.IMAP4_SSL(imap_url) as con:
        con.login(target_email,bad_practice)
        con.select() # defaults to selecting "INBOX"
        # data = con.search(None,"FROM","petersryan84@gmail.com")[1]
        data = con.search(None,"ALL")[1]
        mails = [elem for d in data for elem in d.split()]
        for mail_i in mails:
            em_res,em_data = con.fetch(mail_i,"(RFC822)")
            with BytesIO(em_data[0][1]) as bio:
                email_msg = bytes_parser.parse(bio)
            header_key = "|".join([email_msg["To"],
                                   email_msg["From"],
                                   email_msg["Subject"],
                                   email_msg["Received"],])
            if header_key not in header_keys:
                file_hash = hashlib.sha224(str(header_key).encode("UTF-8"))
                fname = str(emails_dir.joinpath(file_hash.hexdigest()))+".pkl"
                with open(fname,"wb") as f:
                    gc.disable()
                    try:
                        pickle.dump(email_msg,f,protocol=-1)
                    finally:
                        gc.enable()
                # print(f"new email:\n\t{header_key}")
                header_keys[header_key] = fname
    with open(cache_location,"wb") as f:
        gc.disable()
        try:
            pickle.dump(header_keys,f,protocol=-1)
        finally:
            gc.enable()
    # with open(str(cache_location).replace(".pkl",".json"),"w") as f:
    #     json.dump(header_keys,f,indent=4)
