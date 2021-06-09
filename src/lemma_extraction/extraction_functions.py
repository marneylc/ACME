# importing builtin packages
from pathlib import Path
import json
import string
from typing import Union, AnyStr

# importing nltk packages
from nltk.stem import WordNetLemmatizer

# importing sci-kit package's tools for processing text

# importing container/data-structure and plotting packages
import pandas as pd

# custom codebase imports
from src import TABLE_NAMES
from src import project_root_folder
from .cache_class_defs import LemmaDB, lemma_table_row
from .word_extraction_classes import LemmaExtractor
from src.utils.custom_logger import get_logger, CallStackFormatter
from src.body_extraction.cache_class_defs import MessageBodyDB,body_table_row

# creating global namespace variables
info = get_logger("EmailClassifier",__name__+": lemma extraction status",level="INFO")
unexpected_values_logger = get_logger("EmailClassifier",__name__+": unexpected values",formatter=CallStackFormatter,level="WARNING")
inpt_file_encoding = "UTF-8"




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

