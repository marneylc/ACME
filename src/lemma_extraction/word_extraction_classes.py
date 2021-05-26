# importing builtin packages
from sys import stdout
from dataclasses import dataclass, field
from typing import Iterable, List,Tuple, Union, Optional

# importing sci-kit package's tools for processing text
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse.csr import csr_matrix

# importing nltk packages
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk import sent_tokenize
from nltk import word_tokenize
from nltk import pos_tag

# custom codebase imports
from src import src_warning_logger as warning_logger
from src import JPickleSerializable
from src import get_logger
# from src.lemma_extraction import lemma_columns, lemma_table_row


info = get_logger("EmailClassifier",__name__+": Data Extraction Logger",level="INFO")


class TaggerBase(JPickleSerializable):
    @staticmethod
    def word_token_cleanup(tokens):
        for i in range(len(tokens) - 1, 0, -1):
            if "'" in tokens[i]:
                tokens[i - 1] += tokens.pop(i).replace("'", "_^_")
        return " ".join(tokens)


@dataclass(init=False)
class SentenceWordTagger(TaggerBase):
    _subject:List[str]
    _action:List[str]
    _object:List[str]
    _sentence:str = field(repr=False,hash=False,compare=False)
    _word_tokens:List[str] = field(repr=False,hash=False,compare=False)
    _tokens_tagged:List[Tuple[str,str]] = field(repr=False,hash=False,compare=False)

    def __init__(self, sentence_token) -> None:
        super().__init__(
            "_subject",
            "_action",
            "_object",
            "_sentence",
            "_word_tokens",
            "_tokens_tagged",
        )
        self._sentence = sentence_token
        self._word_tokens = list(word_tokenize(sentence_token))
        self._tokens_tagged = pos_tag(self._word_tokens)

    @property
    def subject(self):
        return self._subject

    @property
    def action(self):
        return self._action

    @property
    def object(self):
        return self._object

    @property
    def sentence(self):
        return self._sentence

    @property
    def word_tokens(self):
        return self._word_tokens

    @property
    def tokens_tagged(self):
        return self._tokens_tagged


@dataclass(init=False)
class MessageBodyTagging(TaggerBase):
    _sentence_taggers:List["SentenceWordTagger"]
    _message_body:str
    def __init__(self,message_body:str):
        super().__init__(
            "_sentence_taggers",
            "_message_body"
        )
        self._message_body = message_body
        sent_tokens = [self.word_token_cleanup(sent.split(" ")) for sent in sent_tokenize(message_body)]
        self._sentence_taggers = [SentenceWordTagger(sent) for sent in sent_tokens]


@dataclass(init=False)
class LemmaExtractor(TaggerBase):
    _doc_id:str
    _frequency_sorted_lemma:List[str]
    _frequency_sorted_stopped_lemma:List[str]
    _sentence_tagger:"MessageBodyTagging"=field(repr=False,hash=False,compare=False)
    _body_text:str=field(repr=False,hash=False,compare=False)
    _stopped_lemma:List[str]=field(repr=False,hash=False,compare=False)
    _lemma:List[str]=field(repr=False,hash=False,compare=False)
    _tokenized:List[str]=field(repr=False,hash=False,compare=False)
    _stopped_words:List[str]=field(repr=False,hash=False,compare=False)

    def __init__(self,
                 doc_id:str,
                 body_text:str,
                 excluded_punctuation:str,
                 stopwords_set:set,
                 lemmatizer_ref:WordNetLemmatizer) -> None:
        super().__init__(
            "_doc_id",
            "_frequency_sorted_lemma",
            "_frequency_sorted_stopped_lemma",
            "_body_text",
            "_stopped_lemma",
            "_lemma",
            "_tokenized",
            "_stopped_words",
        )
        self._doc_id = doc_id
        self._body_text = body_text
        tokenized = list(word_tokenize(body_text))
        for i in range(len(tokenized) - 1, 0, -1):
            if len(tokenized[i]) > 30:  # and "/" not in tokenized[i]:
                tokenized.pop(i)
        stopped_words = list(
            filter(lambda token: token not in excluded_punctuation and token.lower() not in stopwords_set, tokenized))
        self.word_token_cleanup(tokenized)
        self.word_token_cleanup(stopped_words)
        # for i in range(len(tokenized) - 1, 0, -1):
        #     if "'" in tokenized[i]:
        #         tokenized[i - 1] += tokenized.pop(i).replace("'", "_^_")
        # for i in range(len(stopped_words) - 1, 0, -1):
        #     if "'" in stopped_words[i]:
        #         stopped_words[i - 1] += stopped_words.pop(i).replace("'", "_^_")
        self._tokenized = tokenized
        self._stopped_words = stopped_words
        self._sentence_tagger = MessageBodyTagging(body_text)
        self._lemma = [lemmatizer_ref.lemmatize(word, pos=wordnet.VERB) for word in tokenized]
        lemma_counts = {}
        for l in self._lemma:
            lemma_counts[l] = lemma_counts.get(l,0)+1
        self._frequency_sorted_lemma = sorted(self._lemma,key=lambda s:lemma_counts[s])
        self._stopped_lemma = [lemmatizer_ref.lemmatize(word, pos=wordnet.VERB) for word in stopped_words]
        lemma_counts = {}
        for l in self._stopped_lemma:
            lemma_counts[l] = lemma_counts.get(l,0)+1
        self._frequency_sorted_stopped_lemma = sorted(self._stopped_lemma,key=lambda s:lemma_counts[s])

    @property
    def doc_id(self):
        return self._doc_id

    @property
    def frequency_sorted_lemma(self):
        return self._frequency_sorted_lemma

    @property
    def frequency_sorted_stopped_lemma(self):
        return self._frequency_sorted_stopped_lemma

    @property
    def body_text(self)->List[str]:
        return self._body_text

    @property
    def tokenized(self)->List[str]:
        return self._tokenized

    @property
    def stopped_words(self)->List[str]:
        return self._stopped_words

    @property
    def lemma(self)->List[str]:
        return self._lemma

    @property
    def stopped_lemma(self)->List[str]:
        return self._stopped_lemma

    def do_all_lemma_join(self,sep:str=" ", repl:Tuple[str]=("_^_", "'")):
        return self.do_join("lemma",sep,repl)

    def do_no_stops_lemma_join(self,sep:str=" ", repl:Tuple[str]=("_^_", "'")):
        return self.do_join("stopped_lemma",sep,repl)

    def do_join(self, attr: str, sep: str, repl:Tuple[str]):
        try:
            target = getattr(self,attr)
            if repl is not None:
                return sep.join(s.replace(*repl) for s in target)
            else:
                return sep.join(target)
        except AttributeError:
            warning_logger.warning(f"Given {attr=} is not a valid attribute of this LemmaExtractor class instance.")
            return ""

    @staticmethod
    def _count_vectorization(data:list) -> Tuple[csr_matrix,List[str]]:
        # <class 'scipy.sparse.csr.csr_matrix'>
        count_vectorizer = CountVectorizer(token_pattern=r"(?u:\b\w\w+\b)")
        bag_of_words = count_vectorizer.fit_transform(data)
        feature_names = count_vectorizer.get_feature_names()
        # print(bag_of_words)
        # print(feature_names)
        # widest = max((len(feat) for feat in feature_names))
        # paired = sorted(zip(feature_names, bag_of_words.data), key=lambda tpl: tpl[1])
        # for feature, count in paired:
        #     print(f"{feature:>{widest}} : {count:>5}", file=fd)
        return bag_of_words, feature_names

    @staticmethod
    def _tf_idf_vectorization(data:list) -> Tuple[csr_matrix,List[str]]:
        tfidf_vectorizer = TfidfVectorizer()
        values = tfidf_vectorizer.fit_transform(data)
        feature_names = tfidf_vectorizer.get_feature_names()
        # widest = max((len(feat) for feat in feature_names))
        # paired = sorted(zip(feature_names, values.data), key=lambda tpl: tpl[1])
        # for feat, val in paired:
        #     print(f"{feat:>{widest}} : {val:>5}", file=fd)
        return values, feature_names

    def to_table_row_dict(self, return_stopped:bool=False):
        if return_stopped:
            lemma = self.stopped_lemma
            joined = self.do_no_stops_lemma_join(repl=None)
        else:
            lemma = self.lemma
            joined = self.do_all_lemma_join(repl=None)
        csr_mat,features = self._count_vectorization([joined])
        counts = {k:v for v,k in zip(csr_mat.data,features)}
        return {"id":self.doc_id, "lemma":lemma, "joined":joined, "counts":counts, "csr_mat":csr_mat, "features":features}
