
# builtin imports
from typing import List, Optional, Union, Tuple, Any, Dict

# project code imports
from src.db_tools.db_class_defs import DBBase, DBBaseException#, DB_SUPPORTED_TYPES
from src.db_tools.db_class_defs import Path # in case we need to do any custom subclassing of Path for DBBase
from src import get_logger, TABLE_NAMES
from src.lemma_extraction import body_columns, body_table_row, body_datapoints_type_mapping
from src.lemma_extraction import lemma_columns, lemma_table_row, lemma_datapoints_type_mapping
# from src import to_list

info_logger = get_logger("EmailClassifier", __name__ + ": Data Extraction Logger", level="INFO")


class MsgBodyDBException(DBBaseException):
    pass


class MessageBodyDB(DBBase):

    def __init__(self,
                 db_path: Optional[Union[bytes,str,Path]] = None,
                 table_names: Optional[Union[List[str], str]] = None,
                 column_names: Optional[Union[List[str], str]] = None,
                 dtype_mapping:Dict[str,Any]=None) -> None:
        if table_names is None:
            table_names = TABLE_NAMES["body"]
        if dtype_mapping is None:
            dtype_mapping = body_datapoints_type_mapping
        if column_names is None:
            column_names = body_columns
        super().__init__(db_path, table_names,column_names, dtype_mapping)

    def add_row(self, table_name: str, db_label: Optional[str] = None, curs_idx: Optional[Tuple[int,int]] = None,
                **column_datas: Dict[str, Any]):
        # ToDo: Wrap execution in try/except block and wrap any DBBaseExceptions in MsgBodyDBException with context msg.
        if db_label is None:
            # db_label = self._table_registry_sql_attrs.get("db_label","")
            db_label = ""
        elif db_label and not db_label.endswith("."):
            db_label += "."
        super().add_row(table_name, db_label, curs_idx, **column_datas)

    def select(self, table_names: Optional[Union[str, List[str]]]=None, column_names: Optional[Union[str, List[str]]] = None,
               filters: Optional[Union[List[str], str]] = None) -> Tuple[str, Any]:
        # ToDo: Wrap execution in try/except block and wrap any DBBaseExceptions in MsgBodyDBException with context msg.
        if not table_names:
            table_names = self.table_names
        row: dict
        for tbl, row in super().select(table_names, column_names, filters):
            _row = body_table_row._make((row.get(k, None) for k in self._column_names[tbl]))
            yield tbl, _row


class LemmaDBException(DBBaseException):
    pass


class LemmaDB(DBBase):

    def __init__(self,
                 db_path: str = None,
                 table_names: Union[List[str], str] = None,
                 column_names: Union[List[str], str] = None,
                 dtype_mapping:Dict[str,Any]=None) -> None:
        if table_names is None:
            table_names = TABLE_NAMES["lemma"]
        if dtype_mapping is None:
            dtype_mapping = lemma_datapoints_type_mapping
        if column_names is None:
            column_names = lemma_columns
        super().__init__(db_path, table_names,column_names, dtype_mapping)

    def add_row(self,
                table_name: str,
                db_label: Optional[str] = None,
                curs_idx: Optional[Tuple[int,int]] = None,
                **column_datas: Dict[str, Any]):
        # ToDo: Wrap execution in try/except block and wrap any DBBaseExceptions in LemmaDBException with context msg.
        if db_label is None:
            # db_label = self._table_registry_sql_attrs.get("db_label","")
            db_label = ""
        elif db_label and not db_label.endswith("."):
            db_label += "."
        super().add_row(table_name, db_label, curs_idx, **column_datas)

    def select(self, table_names: Optional[Union[str, List[str]]]=None, column_names: Optional[Union[str, List[str]]] = None,
               filters: Optional[Union[List[str], str]] = None) -> Tuple[str, Any]:
        # ToDo: Wrap execution in try/except block and wrap any DBBaseExceptions in LemmaDBException with context msg.
        if not table_names:
            table_names = self.table_names
        row: dict
        for tbl, row in super().select(table_names, column_names, filters):
            _row = lemma_table_row._make((row.get(k, None) for k in self._column_names[tbl]))
            yield tbl, _row


