# importing builtin packages
import concurrent.futures as cf
from email.message import EmailMessage
from pathlib import Path
from sys import stdout
import json
import string
from typing import Union, AnyStr, Tuple,List

# importing nltk packages
from nltk.stem import WordNetLemmatizer

# importing sci-kit package's tools for processing text
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse.csr import csr_matrix

# importing container/data-structure and plotting packages
import pandas as pd
import plotly.graph_objs as go

# importing performance and optimization packages
from numba import njit, prange
from numba.typed import List as numbaList

# custom codebase imports
from src import TABLE_NAMES
from src import src_warning_logger as warning_logger
from src import do_pickle, undo_pickle
from src import project_root_folder
from src.email_caching.cache_class_defs import EmailDB, email_table_row
from src.lemma_extraction.cache_class_defs import MessageBodyDB, body_table_row
from src.lemma_extraction.cache_class_defs import LemmaDB, lemma_table_row
from src.lemma_extraction import CustomRegex
from src.lemma_extraction.debugging_tools import allow_debugging,dbg_capture_msg_structures
from src.lemma_extraction.word_extraction_classes import LemmaExtractor
from src.custom_logger import get_logger, CallStackFormatter

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


def plain_body_extraction(msg:EmailMessage, fp=None):
    sample_body = msg.get_body(("plain",))
    if allow_debugging and fp is not None:
        dbg_capture_msg_structures(msg,sample_body,fp)
        print(msg.get_boundary())
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


########################################################################################################################
# Keyword extraction functions
########################################################################################################################
def extract_lemma(targets:list, file_dep:list)->tuple:
    lemmatizer_ref = WordNetLemmatizer()
    # stopwords_set = set(stopwords.words("english"))
    stopwords_set = {"the","be","to","a"}
    # stopwords_set = {}
    excluded_punctuation = string.punctuation
    # excluded_punctuation = ".,"
    email_db_path = Path(file_dep.pop())
    body_db_path = Path(file_dep.pop())
    lemma_db_path = Path(targets.pop())
    # keyword_extraction_path = Path(targets[0])
    # keyword_extraction_path.mkdir(parents=True,exist_ok=True)
    message_bodies = [[],[[],[]],[[],[]],[]]
    # tagged_sentences = []
    extractors = []
    with MessageBodyDB(body_db_path, TABLE_NAMES["body"])("main") as body_db:
        with LemmaDB(lemma_db_path,TABLE_NAMES["lemma"])("main") as lemma_db:
            # curs,curs_pos = lemma_db.cursor
            all_lemma = lemma_db.table_names[0]
            no_stops_lemma = lemma_db.table_names[1]
            existing_lemma = {k:set() for k in lemma_db.table_names}
            row:lemma_table_row
            for table_name,row in lemma_db.select(column_names="id"):
                existing_lemma[table_name].add(row.id)
            row:body_table_row
            for table_name, row in body_db.select(column_names=["id,processed_body"]):
                doc_id = row.id
                body_text = row.processed_body
                keyword_extractor = LemmaExtractor(doc_id,body_text, excluded_punctuation, stopwords_set, lemmatizer_ref)
                extractors.append(keyword_extractor)
                if doc_id not in existing_lemma[all_lemma]:
                    lemma_row_details = keyword_extractor.to_table_row_dict()
                    lemma_db.add_row(all_lemma,"main",**lemma_row_details)
                if doc_id not in existing_lemma[no_stops_lemma]:
                    lemma_row_details = keyword_extractor.to_table_row_dict(True)
                    lemma_db.add_row(no_stops_lemma, "main", **lemma_row_details)
            lemma_db.commit()
                # raw body text
                # message_bodies[0].append(body_text)
                # message_bodies[1][0].append(keyword_extractor.do_join("lemma", " ", ("_^_", "'")))
                # message_bodies[1][1].append(keyword_extractor.lemma)
                # message_bodies[2][0].append(keyword_extractor.do_join("stopped_lemma", " ", ("_^_", "'")))
                # message_bodies[2][1].append(keyword_extractor.stopped_lemma)
                # message_bodies[3].append(f"Subject: '{header['Subject']}'")
    diagnostics = project_root_folder.joinpath("diagnostics")
    diagnostics.mkdir(parents=True,exist_ok=True)
    with open(diagnostics.joinpath("keyword_exctractors.json"),"w") as ext_f:
        json.dump([ext.to_json(4) for ext in extractors],ext_f,indent=4)
    pandas_plotting_inspection(lemma_db_path,email_db_path)
    # with open()
    # _keyword_extraction_helper(message_bodies,keyword_extraction_path, False)

def pandas_plotting_inspection(lemma_db_path:Union[AnyStr,Path], email_db_path:Union[AnyStr,Path],do_plots:bool=True):
    # import plotly.express as px
    pd.options.display.max_columns = 20
    pd.options.display.width = 400
    pd.options.plotting.backend = "plotly"
    with LemmaDB(lemma_db_path,TABLE_NAMES["lemma"]) as lemma_db:
        with lemma_db("email_db",database=email_db_path):
            column_names = lemma_db.column_names["all_lemma"]
            column_names = ",".join(f"t1.{cname}" for cname in column_names[1:])
            agg_sql = f"""
                SELECT 
                    t1.id,t2.subject,{column_names} 
                FROM 
                        main.all_lemma AS t1 
                    JOIN 
                        'email_db'.emails AS t2 
                WHERE 
                    t1.id=t2.id;
                """
            curs, curs_pos = lemma_db.cursor
            curs.arraysize = 10
            agg = []
            curs.execute(agg_sql)
            batch = curs.fetchmany()
            while batch:
                for res in batch:
                    agg.append(res)
                batch = curs.fetchmany()

    # def build_count_dataframe(convert_normed_to_bell:bool=False):
    #     word_bag[0]:csr_matrix
    #     word_bag[1]:List[str]
    #     df = pd.DataFrame(word_bag[0].T.toarray(), index=word_bag[1])
    #     # add_stats_columns(df)
    #     df = df.rename(columns={i: headers[i] for i in range(len(headers))},
    #                    index={k: k.replace("__", "'") for k in df.index},
    #                    errors="raise")
    #     df.insert(len(df.columns), "All Documents", df.max(axis=1))
    #     sortable_map = {k: df.loc[k, "All Documents"] for k in df.index}
    #     df.sort_index(axis=0, inplace=True, key=lambda x: [sortable_map[i] for i in x])
    #     df_normed: pd.DataFrame = df.copy()
    #     df_max = df.sum(axis=0)
    #     for col in df.columns:
    #         df_normed[col] /= df_max[col]
    #     if convert_normed_to_bell:
    #         normed_as_bell_curve(df_normed)
    #     return df,df_normed
    #
    # def normed_as_bell_curve(df_normed):
    #     # now we re-organize df_normed to show as a sort of bell-curve to give visual insight to the
    #     # stdv and var of the word count distribution
    #     normed_sortable_map = {}
    #     indices = tuple(df_normed.index)
    #     end = len(indices)-1
    #     i = 0
    #     try:
    #         for idx in range(0,len(indices),2):
    #             normed_sortable_map[indices[idx]] = i
    #             normed_sortable_map[indices[idx+1]] = end-i
    #             i += 1
    #     except IndexError:
    #         pass
    #     df_normed.sort_index(axis=0, inplace=True, key=lambda x: [normed_sortable_map[i] for i in x])
    #     return
    #
    # def build_figure(df:pd.DataFrame,fig_title,xaxis_title,yaxis_title):
    #     fig = go.Figure()
    #     fig.update_layout(title=fig_title,
    #                       font=dict(
    #                           size=18
    #                       ),
    #                       legend=dict(
    #                           yanchor="top",
    #                           y=.99,
    #                           xanchor="left",
    #                           x=.01,
    #                       ),
    #                       plot_bgcolor="rgba(1,1,1,1)",
    #                       hoverlabel={"namelength":-1,
    #                                   "font_size":16,},
    #                       hovermode="x unified",
    #                       )
    #     col:str
    #     for t, col in zip(df.plot.bar().data, df.columns):
    #         # name will drop the 'Subjec: ' portion of the column label as it's redundant in the plot legend
    #         if col.startswith("Subject: "):
    #             name = col[col.find(": ")+2:]
    #             if len(name)>30:
    #                 name = name[:30]+"..."
    #         else:
    #             name = col
    #         fig.add_bar(x=t.x, y=t.y, name=name)
    #     # # edit axis labels
    #     fig['layout']['xaxis']['title'] = xaxis_title
    #     fig['layout']['yaxis']['title'] = yaxis_title
    #     return fig
    #
    # wb_df,wb_normed = build_count_dataframe()
    # path = out_path.joinpath("raw_word_count_matrix.csv")
    # if path.exists():
    #     warning_logger.warning("Notice!!! We detected that the target csv name on our target path already exists, generating name with a unique id suffix now")
    #     index = 0
    #     path=path.with_name(f"raw_word_count_matrix_{index}.csv")
    #     while path.exists():
    #         index+=1
    #         path = path.with_name(f"raw_word_count_matrix_{index}.csv")
    # info.warning(f"writing word count matrix to:\n\t\t{str(path)}")
    # wb_df.to_csv(str(path))
    # if do_plots:
    #     fig1 = build_figure(wb_normed,
    #                         f"{context_str} Word count as ratios on range [0,1]",
    #                         'Unique words found in documents',
    #                         'Word count as ratio of (unique_word / sum(all_words))')
    #     fig1.show()
    #     fig2 = build_figure(wb_df,
    #                         f"{context_str} Raw word counts",
    #                         'Unique words found in documents',
    #                         'Raw word counts')
    #     fig2.show()


########################################################################################################################
# old keyword extraction approach from before development of sql database pipeline
########################################################################################################################
def parallel_msg_extraction_loop_old(path,body_structs,cached_roots_dir,message_root_map):
    path = Path(path)
    key = path.name
    key = key[:key.rfind(".")]
    with open(path, "rb") as f:
        msg_dict = undo_pickle(f)  # type: dict
    msg: EmailMessage
    msg, body_structure, header = msg_dict["EmailMessage"], msg_dict["body_structure"], msg_dict["header"]
    body_structs[msg["Subject"]] = body_structure
    body = plain_body_extraction(msg, body_structure, header)
    path = cached_roots_dir.joinpath(path.name)
    message_root_map[key] = path
    # modified_body = " ".join((word.replace("'re", " are").replace("'m", " am") for word in body.split(" ")))
    with open(path, "wb") as pkl_f:
        do_pickle({"header": header, "body": body}, pkl_f)


def extract_root_messages_old(targets:list, file_dep:list):
    """

    :param targets: List of absolute path strings pointing to where we should put our output files.
    :param file_dep:
    :return:
    """
    cached_roots_dir = Path(targets[0])
    cached_roots_dir.mkdir(parents=True,exist_ok=True)
    # dbg_structure_path = Path(__file__).resolve().parent.joinpath("debug_structures")
    # dbg_structure_path.mkdir(exist_ok=True)
    message_root_map = {}
    nltk_package_path = file_dep.pop(0)
    body_structs = {}
    with cf.ThreadPoolExecutor() as tpe:
        ftrs = [tpe.submit(parallel_msg_extraction_loop,path,body_structs,cached_roots_dir,message_root_map) for path in file_dep]
        # ftrs = [parallel_msg_extraction_loop(path,body_structs,cached_roots_dir,message_root_map) for path in file_dep]
        cf.wait(ftrs)
    cached_roots_path = cached_roots_dir.joinpath(message_roots_map_fname)
    with open(cached_roots_path,"wb") as f:
        do_pickle(message_root_map,f)


def _count_vectorization(data, fd=stdout)->tuple:
    count_vectorizer = CountVectorizer(token_pattern=r"(?u:\b\w\w+\b)")
    bag_of_words = count_vectorizer.fit_transform(data)
    feature_names = count_vectorizer.get_feature_names()
    # print(bag_of_words)
    # print(feature_names)
    widest = max((len(feat) for feat in feature_names))
    paired = sorted(zip(feature_names, bag_of_words.data), key=lambda tpl: tpl[1])
    for feature, count in paired:
        print(f"{feature:>{widest}} : {count:>5}",file=fd)
    return bag_of_words,feature_names


def _tf_idf_vectorization(data, fd=stdout)->tuple:
    tfidf_vectorizer = TfidfVectorizer()
    values = tfidf_vectorizer.fit_transform(data)
    feature_names = tfidf_vectorizer.get_feature_names()
    widest = max((len(feat) for feat in feature_names))
    paired = sorted(zip(feature_names, values.data), key=lambda tpl: tpl[1])
    for feat,val in paired:
        print(f"{feat:>{widest}} : {val:>5}",file=fd)
    return values,feature_names


def _keyword_extraction_helper(message_bodies:list, path_root:Path, do_plots:bool=True):
    with open("quick_bodies_inspection.json","w") as f:
        json.dump(message_bodies,f,indent=4)
    with open("count_vectorization_output.txt","w") as cv_f:
        word_bag:Tuple[csr_matrix,List[str]] = _count_vectorization(message_bodies[1][0], cv_f)
    with open("tf_idf_vectorization_output.txt","w") as tfidf_f:
        tf_idf:Tuple[csr_matrix,List[str]] = _tf_idf_vectorization(message_bodies[1][0], tfidf_f)
    with open("count_vectorization_output_stopped.txt","w") as cv_f:
        word_bag_stopped = _count_vectorization(message_bodies[2][0], cv_f)
    with open("tf_idf_vectorization_output_stopped.txt","w") as tfidf_f:
        tf_idf_stopped = _tf_idf_vectorization(message_bodies[2][0], tfidf_f)
    # print("now to show figures")
    # pandas_plotting_inspection(word_bag, tf_idf, message_bodies[3], "with stop-words")
    pandas_plotting_inspection_old(word_bag_stopped, tf_idf_stopped, message_bodies[3], "without stop-words", path_root, do_plots=do_plots)


def pandas_plotting_inspection_old(word_bag:Tuple[csr_matrix,List[str]], tf_idf:Tuple[csr_matrix,List[str]], headers:list, context_str:str, out_path:Path, do_plots:bool=True):
    # import plotly.express as px
    pd.options.display.max_columns = 20
    pd.options.display.width = 400
    pd.options.plotting.backend = "plotly"

    def build_count_dataframe():
        df = pd.DataFrame(word_bag[0].T.toarray(), index=word_bag[1])
        # add_stats_columns(df)
        df = df.rename(columns={i: headers[i] for i in range(len(headers))},
                       index={k: k.replace("__", "'") for k in df.index},
                       errors="raise")
        df.insert(len(df.columns), "All Documents", df.max(axis=1))
        sortable_map = {k: df.loc[k, "All Documents"] for k in df.index}
        df.sort_index(axis=0, inplace=True, key=lambda x: [sortable_map[i] for i in x])
        df_normed: pd.DataFrame = df.copy()
        df_max = df.sum(axis=0)
        for col in df.columns:
            df_normed[col] /= df_max[col]
        # now we re-organize df_normed to show as a sort of bell-curve to give visual insight to the
        # stdv and var of the word count distribution
        # normed_sortable_map = {}
        # indices = tuple(df_normed.index)
        # end = len(indices)-1
        # i = 0
        # try:
        #     for idx in range(0,len(indices),2):
        #         normed_sortable_map[indices[idx]] = i
        #         normed_sortable_map[indices[idx+1]] = end-i
        #         i += 1
        # except IndexError:
        #     pass
        # df_normed.sort_index(axis=0, inplace=True, key=lambda x: [normed_sortable_map[i] for i in x])
        return df,df_normed

    def build_figure(df:pd.DataFrame,fig_title,xaxis_title,yaxis_title):
        fig = go.Figure()
        fig.update_layout(title=fig_title,
                          font=dict(
                              size=18
                          ),
                          legend=dict(
                              yanchor="top",
                              y=.99,
                              xanchor="left",
                              x=.01,
                          ),
                          plot_bgcolor="rgba(1,1,1,1)",
                          hoverlabel={"namelength":-1,
                                      "font_size":16,},
                          hovermode="x unified",
                          )
        col:str
        for t, col in zip(df.plot.bar().data, df.columns):
            # name will drop the 'Subjec: ' portion of the column label as it's redundant in the plot legend
            if col.startswith("Subject: "):
                name = col[col.find(": ")+2:]
                if len(name)>30:
                    name = name[:30]+"..."
            else:
                name = col
            fig.add_bar(x=t.x, y=t.y, name=name)
        # # edit axis labels
        fig['layout']['xaxis']['title'] = xaxis_title
        fig['layout']['yaxis']['title'] = yaxis_title
        return fig

    wb_df,wb_normed = build_count_dataframe()
    path = out_path.joinpath("raw_word_count_matrix.csv")
    if path.exists():
        warning_logger.warning("Notice!!! We detected that the target csv name on our target path already exists, generating name with a unique id suffix now")
        index = 0
        path=path.with_name(f"raw_word_count_matrix_{index}.csv")
        while path.exists():
            index+=1
            path = path.with_name(f"raw_word_count_matrix_{index}.csv")
    info.warning(f"writing word count matrix to:\n\t\t{str(path)}")
    wb_df.to_csv(str(path))
    if do_plots:
        fig1 = build_figure(wb_normed,
                            f"{context_str} Word count as ratios on range [0,1]",
                            'Unique words found in documents',
                            'Word count as ratio of (unique_word / sum(all_words))')
        fig1.show()
        fig2 = build_figure(wb_df,
                            f"{context_str} Raw word counts",
                            'Unique words found in documents',
                            'Raw word counts')
        fig2.show()
