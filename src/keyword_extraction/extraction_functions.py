# importing builti packages
from collections import namedtuple
import concurrent.futures as cf
from email.message import EmailMessage
from pathlib import Path
import re
from sys import stdout
import json

# importing nltk packages
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk import sent_tokenize
from nltk import word_tokenize
from nltk import pos_tag

# importing processed text assistance tools
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

# importing container and data structure packages
import pandas as pd
import plotly.graph_objs as go

# importing performance and optimization packages
from numba import njit, prange
from numba.typed import List as numbaList


# custom codebase imports
from src import src_warning_logger as warning_logger
from src import do_pickle, un_pickle
from src.word_classification.word_extraction_classes import SentenceWordTagger, KeywordExtractor

# creating global namespace variables
inpt_file_encoding = "UTF-8"
fnames_tpl = namedtuple("target_fnames",["keywords","signatures","participants"])
output_target_files = fnames_tpl._make(("keywords.pkl","signatures.pkl","participants.pkl"))
message_roots_cache_dir = "message_roots",
message_roots_map_fname = "cached_roots_map.pkl"
cached_email_bodies = {}

# creating compiled regex patterns for text manipulation and classification prep
# NOTE: the names of all regex variables start with re_
re_condense_multi_newline_pattern = re.compile("(?:(\s*)\n(\s*))+")
re_get_carriage_return = re.compile("(\r\n*)")
re_linebreak_fix = re.compile("=(?:(?:\n)|(?:\r\n))")
re_plain_text_divider = re.compile("_{10,}")
re_id_extraction = re.compile("(x_)+Signature")
re_header_content = re.compile("(?P<line>(?P<key>\w+):\s*(?P<value>.+))")
re_abstract_header_block = re.compile("(From:(?:.*\n)+?Subject:.*\n)",re.MULTILINE)
re_start_of_text_unicode = re.compile("<?\u0002>?")
# url capture regex taken from: https://gist.github.com/gruber/8891611
re_url_capture = re.compile(r"(?i)\b((https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))",re.MULTILINE)


ESC_SEQ = "\033["
charc = 90  # charcoal
purp = 35  # purple
green = 32  # green -- might be just my eyes, but green(32) and yellow(33) look almost identical
dull_cyan = 36  # dull-cyan
bright_purp = 95  # bright-purple
bright_red = 91  # bright-red
RESET = ESC_SEQ + "0m"
formatted_red = f"{ESC_SEQ}1;{bright_red}m"
formatted_green = f"{ESC_SEQ}1;{green}m"
target_match = formatted_green
non_target_match = f"{ESC_SEQ}1;{dull_cyan}m"

allow_debugging = False # True
dbg_id_to_look_for = r"e03b018e3df65eb5dde6fafcec5447c10e120f5d298f82959a402235"
dbg_active_id = ""


def dbg_structure(root,msg, level=0, include_default=False):
    """A handy debugging aid"""
    tab = ' ' * (level * 4)
    ret = []
    # if fp==out_fd:
    #     color_format = target_match if root is msg else non_target_match
    #     reset = RESET
    # else:
    #     color_format = "* " if root is msg else ""
    #     reset = " *" if color_format else ""
    ret.append({"str":f"{tab} {{color_format}}{root.get_content_type()}{{suffix}}","suffix":(f' [{root.get_default_type()}]{{reset}}' if include_default else "{reset}"),"is_target":root is msg})
    if root.is_multipart():
        for subpart in root.get_payload():
            ret.extend(dbg_structure(subpart,msg, level+1, include_default))
    return ret


def dbg_capture_msg_structures(msg,sample_body0,file_descriptors:list=None):
    fp = file_descriptors if file_descriptors is not None else []
    result = dbg_structure(msg, sample_body0)
    print_out = [stdout] if fp is None else [stdout, *fp]
    intro = f"\n\n{'':=<120}\nSubject: '{msg.get('Subject', 'subject is None')}'\n{{encoding}}\n{'':=<120}"
    for fd in print_out:
        print(intro.format(encoding=fd.encoding), file=fd)
    for d in result:
        s = d.pop("str")
        is_target = d.pop("is_target")
        suffix = d.pop("suffix")
        for out in print_out:
            if out.encoding.lower() == "utf-8":
                color_format = target_match if is_target else non_target_match
                reset = RESET
            else:
                color_format = "* " if is_target else ""
                reset = " *" if is_target else ""
            print(s.format(color_format=color_format, suffix=suffix.format(reset=reset)), file=out)
    for fd in print_out:
        print(file=fd)


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


def plain_body_extraction(msg:EmailMessage, body_structure, header,fp=None):
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
    links = re_url_capture.search(sample_body)
    # print(f"{msg['Subject']}\n\t{links=}")
    sample_body = re_url_capture.sub("\2",sample_body)
    sample_body = re_start_of_text_unicode.sub("",sample_body)
    header_matches = re_abstract_header_block.search(sample_body)
    end = -1
    while header_matches:
        end = header_matches.end()
        test = sample_body[end:]
        header_matches = re_abstract_header_block.search(sample_body,end)
    init_end = end
    while -1 < end < len(sample_body):
        end += 1
        if sample_body[end].strip():
            break
    else:
        end = max(min(init_end, len(sample_body) - 1),0)
    sample_body = sample_body[end:]
    sample_body = re_linebreak_fix.sub("", sample_body)#.split("\n")
    # ToDo: We are removing empty lines here, but maybe we should also record their positioning for later analysis?
    sample_body = re_get_carriage_return.sub("\n", sample_body).split("\n")
    sample_body = [line for line in sample_body if line.strip()]
    sample_body = "\n".join(sample_body)
    # sample_body = re_plain_text_divider.split(sample_body)[-1] # meant to extract only the root message.
    # return sample_body,charset
    return sample_body


def parallel_msg_extraction_loop(path,body_structs,cached_roots_dir,message_root_map):
    path = Path(path)
    key = path.name
    key = key[:key.rfind(".")]
    with open(path, "rb") as f:
        msg_dict = un_pickle(f)  # type: dict
    msg: EmailMessage
    msg, body_structure, header = msg_dict["EmailMessage"], msg_dict["body_structure"], msg_dict["header"]
    body_structs[msg["Subject"]] = body_structure
    body = plain_body_extraction(msg, body_structure, header)
    path = cached_roots_dir.joinpath(path.name)
    message_root_map[key] = path
    # modified_body = " ".join((word.replace("'re", " are").replace("'m", " am") for word in body.split(" ")))
    with open(path, "wb") as pkl_f:
        do_pickle({"header": header, "body": body}, pkl_f)


def extract_root_messages(targets:list, file_dep:list):
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


def extract_keywords(targets:list, file_dep:list)->tuple:
    lemmatizer_ref = WordNetLemmatizer()
    # stopwords_set = set(stopwords.words("english"))
    stopwords_set = {"the","be","to","a"}
    # stopwords_set = {}
    # excluded_punctuation = string.punctuation
    excluded_punctuation = ".,"
    keyword_extraction_path = Path(targets[0])
    keyword_extraction_path.mkdir(parents=True,exist_ok=True)
    message_bodies = [[],[[],[]],[[],[]],[]]
    tagged_sentences = []
    extractors = []
    for path in file_dep[1:]:
        path = Path(path)
        with open(path,"rb") as f:
            d = un_pickle(f)
            body_text = d["body"]
            header = d["header"]
        # tagged_sentences.append(sent_tags)
        if body_text:
            keyword_extractor = KeywordExtractor(body_text,excluded_punctuation,stopwords_set,lemmatizer_ref)
            extractors.append(keyword_extractor)
            message_bodies[0].append(body_text)
            message_bodies[1][0].append(keyword_extractor.do_join("lemma", " ", ("_^_", "'")))
            message_bodies[1][1].append(keyword_extractor.lemma)
            message_bodies[2][0].append(keyword_extractor.do_join("stopped_lemma", " ", ("_^_", "'")))
            message_bodies[2][1].append(keyword_extractor.stopped_lemma)
            message_bodies[3].append(f"Subject: '{header['Subject']}'")
        else:
            print(f"for the following path, the body text string was empty:\n\t{path=}\n\t{header['Subject']=}\n\t{body_text=}")

    with open("keyword_exctractors.json","w") as ext_f:
        json.dump([ext.to_json(4) for ext in extractors],ext_f,indent=4)
    # with open()
    _keyword_extraction_helper(message_bodies,keyword_extraction_path)


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


def _keyword_extraction_helper(message_bodies:list, path_root:Path):
    with open("quick_bodies_inspection.json","w") as f:
        json.dump(message_bodies,f,indent=4)
    with open("count_vectorization_output.txt","w") as cv_f:
        word_bag = _count_vectorization(message_bodies[1][0], cv_f)
    with open("tf_idf_vectorization_output.txt","w") as tfidf_f:
        tf_idf = _tf_idf_vectorization(message_bodies[1][0], tfidf_f)
    with open("count_vectorization_output_stopped.txt","w") as cv_f:
        word_bag_stopped = _count_vectorization(message_bodies[2][0], cv_f)
    with open("tf_idf_vectorization_output_stopped.txt","w") as tfidf_f:
        tf_idf_stopped = _tf_idf_vectorization(message_bodies[2][0], tfidf_f)
    # print("now to show figures")
    # plotting_do_pandas_inspection(word_bag, tf_idf, message_bodies[3], "with stop-words")
    plotting_do_pandas_inspection(word_bag_stopped, tf_idf_stopped, message_bodies[3], "without stop-words",path_root)


def plotting_do_pandas_inspection(word_bag, tf_idf, headers:list, context_str:str, out_path:Path):
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
    wb_df.to_csv(out_path.joinpath("raw_word_count_matrix.csv"))
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
