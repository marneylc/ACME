from pathlib import Path
import pickle
import gc
from email.message import EmailMessage
import re
from sys import stdout
from collections import namedtuple
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import string
# import json

inpt_file_encoding = "UTF-8"
fnames_tpl = namedtuple("target_fnames",["keywords","signatures","participants"])#
output_target_files = fnames_tpl._make(("keywords.pkl","signatures.pkl","participants.pkl"))
message_roots_cache_dir = "message_roots",
message_roots_map_fname = "cached_roots_map.pkl"
cached_email_bodies = {}
re_condense_multi_newline_pattern = re.compile("(?:(\s*)\n(\s*))+")
re_get_carriage_return = re.compile("(\r\n*)")
re_linebreak_fix = re.compile("=(?:(?:\n)|(?:\r\n))")
re_plain_text_divider = re.compile("_{10,}")
re_id_extraction = re.compile("(x_)+Signature")
re_header_content = re.compile("(?P<line>(?P<key>\w+):\s*(?P<value>.+))")
re_abstract_header_block = re.compile("(From:(?:.*\n)+?Subject:.*\n)",re.MULTILINE)

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


def un_pickle(fd):
    gc.disable()
    try:
        return pickle.load(fd)
    finally:
        gc.enable()


def do_pickle(obj,fd):
    gc.disable()
    try:
        pickle.dump(obj,fd,protocol=-1)
    finally:
        gc.enable()


def plain_body_extraction(msg:EmailMessage, body_structure, header,fp=None):
    sample_body = msg.get_body(("plain",))
    if allow_debugging and fp is not None:
        dbg_capture_msg_structures(msg,sample_body,fp)
        print(msg.get_boundary())
    if "Content-Transfer-Encoding" in sample_body.keys():
        encoding = sample_body['Content-Transfer-Encoding']
        do_decode = encoding == "base64"
    else:
        encoding = None
        do_decode = False
    charset = sample_body.get('Content-Type'," charset=\"utf-8-sig\"").split("charset=")[-1].split(';')[0].strip("\"").lower()
    sample_body = sample_body.get_payload(decode=do_decode)
    if isinstance(sample_body,bytes):
        sample_body1:bytes
        sample_body = sample_body.decode(encoding=charset)
    else:
        sample_body = sample_body
    header_matches = re_abstract_header_block.search(sample_body)
    end = -1
    while header_matches:
        end = header_matches.end()
        header_matches = re_abstract_header_block.search(sample_body,end)
    init_end = end
    while end>-1 and end < len(sample_body):
        end += 1
        if sample_body[end] != "\n":
            break
    else:
        end = min(init_end, len(sample_body) - 1)
    sample_body = sample_body[end:]
    sample_body = re_linebreak_fix.sub("", sample_body)#.split("\n")
    sample_body = re_get_carriage_return.sub("\n", sample_body).split("\n")
    sample_body = [line for line in sample_body if line.strip()]
    sample_body = "\n".join(sample_body)
    sample_body = re_plain_text_divider.split(sample_body)[-1]
    # return sample_body,charset
    return sample_body


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
    for path in file_dep:
        path = Path(path)
        key = path.name
        key = key[:key.rfind(".")]
        with open(path, "rb") as f:
            msg_dict = un_pickle(f) # type: dict
        msg:EmailMessage
        msg, body_structure, header = msg_dict["EmailMessage"], msg_dict["body_structure"],msg_dict["header"]
        body = plain_body_extraction(msg,body_structure,header)
        path = cached_roots_dir.joinpath(path.name)
        message_root_map[key] = path
        # modified_body = " ".join((word.replace("'re", " are").replace("'m", " am") for word in body.split(" ")))
        with open(path,"wb") as pkl_f:
            do_pickle(body,pkl_f)
    cached_roots_path = cached_roots_dir.joinpath(message_roots_map_fname)
    with open(cached_roots_path,"wb") as f:
        do_pickle(message_root_map,f)


def extract_keywords(targets:list, file_dep:list)->tuple:
    def count_vectorization(i,fd=stdout)->None:
        count_vectorizer = CountVectorizer()
        bag_of_words = count_vectorizer.fit_transform(message_bodies[i])
        feature_names = count_vectorizer.get_feature_names()
        # print(bag_of_words)
        # print(feature_names)
        widest = max((len(feat) for feat in feature_names))
        paired = sorted(zip(feature_names, bag_of_words.data), key=lambda tpl: tpl[1])
        for feat, count in paired:
            print(f"{feat:>{widest}} : {count:>5}",file=fd)
        return bag_of_words,feature_names

    def tf_idf_vectorization(i,fd=stdout)->tuple:
        tfidf_vectorizer = TfidfVectorizer()
        values = tfidf_vectorizer.fit_transform(message_bodies[i])
        feature_names = tfidf_vectorizer.get_feature_names()
        widest = max((len(feat) for feat in feature_names))
        paired = sorted(zip(feature_names, values.data), key=lambda tpl: tpl[1])
        for feat,val in paired:
            print(f"{feat:>{widest}} : {val:>5}",file=fd)
        return values,feature_names

    lemmatizer_ref = WordNetLemmatizer()
    stopwords_set = set(stopwords.words("english"))
    # stopwords_set = {"the","be","to","a"}
    keyword_extraction_path = Path(targets[0])
    keyword_extraction_path.mkdir(parents=True,exist_ok=True)
    message_bodies = [[],[],[]]
    no_dupes = set()
    for path in file_dep[1:]:
        with open(path,"rb") as f:
            s = un_pickle(f)
        if s:
            tokenized = list(filter(lambda token: token not in string.punctuation and token.lower() not in stopwords_set,word_tokenize(s,"english",preserve_line=False)))
            for i in range(len(tokenized)-1,0,-1):
                if tokenized[i] in ("'m","'re"):
                    tokenized[i-1] += tokenized.pop(i)
                    if tokenized[i].lower() == "helium" and path not in no_dupes:
                        print(path)
                        no_dupes.add(path)
            widest = max((len(w) for w in tokenized))
            if widest>30:
                continue
            lemma = [lemmatizer_ref.lemmatize(word,pos=wordnet.VERB) for word in tokenized]
            message_bodies[0].append(s)
            message_bodies[1].append(" ".join(lemma))
            message_bodies[2].append(lemma)

    import json
    with open("quick_bodies_inspection.json","w") as f:
        json.dump(message_bodies,f,indent=4)
    with open("count_vectorization_output.txt","w") as cv_f:
        word_bag = count_vectorization(1,cv_f)

    with open("tf_idf_vectorization_output.txt","w") as tfidf_f:
        tf_idf = tf_idf_vectorization(1,tfidf_f)
    dbg_do_pandas_inspection(word_bag,tf_idf)


def dbg_do_pandas_inspection(word_bag,tf_idf):
    import pandas as pd
    from plotly.subplots import make_subplots
    import plotly.graph_objs as go
    pd.options.display.max_columns = 20
    pd.options.display.width = 400
    pd.options.plotting.backend = "plotly"
    def add_stats_columns(df:pd.DataFrame)->None:
        ops = [
            ("Summed",df.sum(axis=1)),
            ("Averaged",df.mean(axis=1)),
            ("Min",df.min(axis=1)),
            ("midx",df.idxmin(axis=1)),
            ("Median",df.median(axis=1)),
            ("Mode",df.mode(axis=1).mean(axis=1,numeric_only=True)),
            ("Max",df.max(axis=1)),
            ("Midx",df.idxmax(axis=1)),
        ]
        for col_name,values in ops:
            df.insert(len(df.columns),col_name,values)
        return

    wb_df = pd.DataFrame(word_bag[0].T.toarray(),index=word_bag[1])
    tfidf_df = pd.DataFrame(tf_idf[0].T.toarray(),index=tf_idf[1])

    add_stats_columns(wb_df)
    add_stats_columns(tfidf_df)
    sortable_map = {k:tfidf_df.loc[k,"Max"] for k in tfidf_df.index}
    wb_df.sort_index(axis=0,inplace=True,key=lambda x:[sortable_map[i] for i in x])
    tfidf_df.sort_index(axis=0,inplace=True,key=lambda x:[sortable_map[i] for i in x])
    tf_normed = tfidf_df.copy()
    wb_normed = wb_df.copy()
    tf_max = tfidf_df.max(axis=0)
    wb_max = wb_df.max(axis=0)
    for col in tfidf_df.columns:
        tf_normed[col] /= tf_max[col]
        wb_normed[col] /= wb_max[col]
    normalized = wb_normed - tf_normed
    # normalized += pd.DataFrame.abs(normalized.min(axis=0))

    tfidf_df.rename({k:f"tf-{k}" for k in tfidf_df.columns},axis="columns")
    wb_df.rename({k:f"wb-{k}" for k in wb_df.columns},axis="columns")

    fig1 = make_subplots(2, 1,subplot_titles=("tf-idf data","word bag data"))
    for t in tf_normed.plot.line().data:
        fig1.add_trace(t,row=1,col=1)
    for t in wb_normed.plot.line().data:
        fig1.add_trace(t,row=2,col=1)

    fig2 = make_subplots(2,1,subplot_titles=("line plots","bar plots"))
    for t in normalized.plot.line().data:
        fig2.add_trace(t,row=1,col=1)
    for t in normalized.plot.bar().data:
        fig2.add_trace(t, row=2, col=1)

    fig3 = go.Figure()
    fig3.update_layout(title="Big bar plot")
    markers_d = dict(mode="lines+markers",line=dict(width=1))
    for t1,t2 in zip(tf_normed.plot.line().data,wb_normed.plot.line().data):
        t1_slopes = [0]*len(t1.x)
        t2_slopes = t1_slopes[:]
        diff_slope = t1_slopes[:]
        diff = t2.y-t1.y
        for i in range(1,len(t1.x)):
            t1_slopes[i] += t1.y[i]-t1.y[i-1]
            t2_slopes[i] += t2.y[i]-t2.y[i-1]
            diff_slope[i] += diff[i]-diff[i-1]

        fig3.add_scattergl(x=t1.x,y=t1.y,name=t1.name+"_tf",**markers_d)
        fig3.add_scattergl(x=t1.x,y=t1_slopes,name=t1.name+"_tf_slope",**markers_d)

        fig3.add_scattergl(x=t2.x,y=t2.y,name=t2.name+"_wb",**markers_d)
        fig3.add_scattergl(x=t2.x,y=t2_slopes,name=t2.name+"_wb_slope",**markers_d)

        fig3.add_scattergl(x=t2.x,y=diff,name=t2.name+"_diff",**markers_d)
        fig3.add_scattergl(x=t2.x,y=diff_slope,name=t2.name+"_diff_slope",**markers_d)


    print("now to show figures")
    fig1.show()
    fig2.show()
    fig3.show()
    print(f"diffs:\n{normalized}\n\n")
    print(f"tf_normed:\n{tf_normed}\n\n")
    print(f"wb_normed:\n{wb_normed}\n\n")
    # print(f"word bag data frame:\n{formatted_red}{wb_df.loc[:,:8]}{RESET}\n\n")
    # print(f"word bag data frame:\n{formatted_red}{wb_df.loc[:,'Summed':]}{RESET}\n\n")
    # print(f"tf-idf data frame:\n{formatted_green}{tfidf_df.loc[:,:8]}{RESET}\n\n")
    # print(f"tf-idf data frame:\n{formatted_green}{tfidf_df.loc[:,'Summed':]}{RESET}\n\n")
    # input("press enter to end script execution")
    dbg_break = 0
