# importing builti packages
from dataclasses import dataclass, field
import gc
import pickle
from typing import Iterable, List,Tuple
import json

# importing nltk packages
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk import sent_tokenize
from nltk import word_tokenize
from nltk import pos_tag

# importing serialization assistance packages
from jsonpickle import encode as jp_encode, decode as jp_decode

# custom codebase imports
from src import src_warning_logger as warning_logger


@dataclass(init=False)
class JPickleSerializable:
    _my_attrs:List[str]

    def __init__(self, *class_attrs:List[str]):
        self._my_attrs = class_attrs

    def to_json(self, indent:int):
        try:
            if gc.isenabled():
                gc.disable()
            return jp_encode(self, indent=indent)
        finally:
            if not gc.isenabled():
                gc.enable()


@dataclass(init=False)
class SentenceWordTagger(JPickleSerializable):
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
class MessageBodyTagging(JPickleSerializable):
    _sentence_taggers:List["SentenceWordTagger"]
    _message_body:str
    def __init__(self,message_body:str):
        super().__init__(
            "_sentence_taggers",
            "_message_body"
        )
        self._message_body = message_body
        sent_tokens = [word_token_cleanup(sent.split(" ")) for sent in sent_tokenize(message_body)]
        self._sentence_taggers = [SentenceWordTagger(sent) for sent in sent_tokens]


@dataclass(init=False)
class KeywordExtractor(JPickleSerializable):
    _frequency_sorted_lemma:List[str]
    _frequency_sorted_stopped_lemma:List[str]
    _sentence_tagger:"MessageBodyTagging"
    _body_text:str
    _stopped_lemma:List[str]
    _lemma:List[str]
    _tokenized:List[str]
    _stopped_words:List[str]

    def __init__(self,
                 body_text:str,
                 excluded_punctuation:str,
                 stopwords_set:set,
                 lemmatizer_ref:WordNetLemmatizer) -> None:
        super().__init__(
            "_frequency_sorted_lemma",
            "_frequency_sorted_stopped_lemma",
            "_body_text",
            "_stopped_lemma",
            "_lemma",
            "_tokenized",
            "_stopped_words",
        )
        self._body_text = body_text
        tokenized = list(word_tokenize(body_text))
        for i in range(len(tokenized) - 1, 0, -1):
            if len(tokenized[i]) > 30:  # and "/" not in tokenized[i]:
                tokenized.pop(i)
        stopped_words = list(
            filter(lambda token: token not in excluded_punctuation and token.lower() not in stopwords_set, tokenized))
        word_token_cleanup(tokenized)
        word_token_cleanup(stopped_words)
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

    def do_join(self, attr: str, sep: str, repl:Iterable=None):
        try:
            target = getattr(self,attr)
            if repl is not None:
                return sep.join(s.replace(*repl) for s in getattr(self,attr))
            else:
                return sep.join(s for s in getattr(self, attr))
        except AttributeError:
            warning_logger.warning(f"Given {attr=} is not a valid attribute of this KeywordExtractor class instance.")
            return ""


def word_token_cleanup(tokens):
    for i in range(len(tokens) - 1, 0, -1):
        if "'" in tokens[i]:
            tokens[i - 1] += tokens.pop(i).replace("'", "_^_")
    return " ".join(tokens)