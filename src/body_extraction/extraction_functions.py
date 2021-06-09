# importing builtin packages
import concurrent.futures as cf
from email.message import EmailMessage
from pathlib import Path

# importing performance and optimization packages
from numba import njit, prange
from numba.typed import List as numbaList

# custom codebase imports
from src import TABLE_NAMES
from src.email_caching.cache_class_defs import EmailDB, email_table_row
from src.body_extraction.cache_class_defs import MessageBodyDB
from src.body_extraction import CustomRegex
from src.utils.custom_logger import get_logger, CallStackFormatter

# creating global namespace variables
info = get_logger("EmailClassifier",__name__+": lemma extraction status",level="INFO")
unexpected_values_logger = get_logger("EmailClassifier",__name__+": unexpected values",formatter=CallStackFormatter,level="WARNING")
inpt_file_encoding = "UTF-8"
message_roots_cache_dir = "message_roots",
message_roots_map_fname = "cached_roots_map.pkl"
cached_email_bodies = {}
regex = CustomRegex()


########################################################################################################################
# message body extraction functions
########################################################################################################################
@njit(parallel=True,nogil=True)
def numba_str_replace(words:str):
    word_lst = numbaList()
    for w in words.replace("\r\n"," \n").split(" "):
        word_lst.append(w)
    for i in prange(len(word_lst)):
        wrd = list(word_lst[i])
        for j,c in enumerate(wrd):
            if wrd[j] in ("=92",u"\u2019",u"\u2018"):
                wrd[j] = "'"
            elif wrd[j]==u"\ufeff":
                wrd[j] = " "
            elif wrd[j]==u"\u2014":
                wrd[j] = "--"
        word_lst[i] = "".join(wrd)
        # word_lst[i][j] = word_lst[i].replace("=92","'").replace(u"\u2019","'").replace(u"\u2018","'").replace(u"\ufeff","")
    for i in range(len(word_lst)-2,0,-1):
        if word_lst[i]=="'":
            quote = word_lst.pop(i)
            quote += word_lst.pop(i)
            word_lst[i-1] += quote
    return " ".join(word_lst)


def plain_body_extraction(msg:EmailMessage):
    sample_body = msg.get_body(("plain",))
    charset = sample_body.get('Content-Type'," charset=\"utf-8-sig\"").split("charset=")[-1].split(';')[0].strip("\"").lower()
    sample_body = sample_body.get_payload(decode=True)
    if isinstance(sample_body,bytes):
        # sample_body = sample_body.decode(encoding=charset)
        sample_body = sample_body.decode(charset).encode("unicode_escape").decode("unicode_escape")
    else:
        sample_body = sample_body.encode("unicode_escape").decode("unicode_escape")
    sample_body = sample_body.replace("=92","'").replace(u"\u2019","'").replace(u"\u2018","'").replace(u"\u2014","--").replace(u"\ufeff","")
    # links = re_url_capture.search(sample_body)
    # print(f"{msg['Subject']}\n\t{links=}")
    sample_body = regex.re_url_capture.sub("\2",sample_body)
    sample_body = regex.re_start_of_text_unicode.sub("",sample_body)
    raw_corrected_body = sample_body[:]
    header_matches = regex.re_abstract_header_block.search(sample_body)
    end = -1
    while header_matches:
        end = header_matches.end()
        # test = sample_body[end:]
        header_matches = regex.re_abstract_header_block.search(sample_body,end)
    init_end = end
    while -1 < end < len(sample_body):
        end += 1
        if sample_body[end].strip():
            break
    else:
        end = max(min(init_end, len(sample_body) - 1),0)
    sample_body = sample_body[end:]
    sample_body = regex.re_linebreak_fix.sub("", sample_body)#.split("\n")
    # ToDo: We are removing empty lines here, but maybe we should also record their positioning for later analysis?
    sample_body = regex.re_get_carriage_return.sub("\n", sample_body).split("\n")
    sample_body = [line for line in sample_body if line.strip()]
    sample_body = "\n".join(sample_body)
    # sample_body = re_plain_text_divider.split(sample_body)[-1] # meant to extract only the root message.
    # return sample_body,charset
    return raw_corrected_body,sample_body


def parallel_msg_extraction_loop(email_row_data:email_table_row):
    raw_body,processed_body = plain_body_extraction(email_row_data.email_item.email_msg)
    # add_row(self, table_name: str, db_label: Optional[str] = None, curs_idx: tuple = None, **row_obj: dict)
    # add_row(TABLE_NAMES["body"][0],processed_body=processed_body,raw_body=raw_body)
    return email_row_data.id,raw_body, processed_body


def extract_root_messages(targets:list, file_dep:list):
    """

    :param targets: List of absolute path strings pointing to where we should put our output files.
    :param file_dep:
    :return:
    """
    nltk_package_path = file_dep.pop(0)
    cached_emails = Path(file_dep.pop(0))
    cached_msg_bodies = Path(targets.pop(0))
    cached_msg_bodies.parent.mkdir(parents=True,exist_ok=True)
    with EmailDB(cached_emails,TABLE_NAMES["email"])("main") as email_db:
        with MessageBodyDB(cached_msg_bodies, TABLE_NAMES["body"])("main") as body_db:
            existing_bodies = set(row.id for _,row in body_db.select(body_db.table_names[0],"id"))
            with cf.ThreadPoolExecutor() as tpe:
                ftrs = [tpe.submit(parallel_msg_extraction_loop,row)
                        for _,row in email_db.select(TABLE_NAMES["email"][0])
                        if row.id not in existing_bodies]
                # ftrs = [parallel_msg_extraction_loop(path,body_structs,cached_roots_dir,message_root_map) for path in file_dep]
                for ftr in cf.as_completed(ftrs):
                    if not ftr.exception():
                        row_id, raw_body, processed_body = ftr.result()
                        info.info(f"adding new row to body_db for email_db row-id: {row_id}")
                        body_db.add_row(body_db.table_names[0], "main", id=row_id, raw_body=raw_body,processed_body=processed_body)
            body_db.commit()


    # cached_roots_path = cached_roots_dir.joinpath(message_roots_map_fname)
    # with open(cached_roots_path,"wb") as f:
    #     do_pickle(message_root_map,f)


