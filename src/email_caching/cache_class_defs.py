# builtin imports
from dataclasses import dataclass, field
from typing import List, Optional, Union, Tuple, Any, Dict
from email.message import EmailMessage

# custom code imports
from src.db_tools.db_class_defs import DBBase, DBBaseException
from src.db_tools.db_class_defs import Path # in case we need to do any custom subclassing of Path for DBBase
from src import JPickleSerializable
from src import get_logger
from src.email_caching import email_table_row, email_table_columns, data_point_translations, email_datapoints_type_mapping

info = get_logger("EmailClassifier",__name__+": Email DB logger",level="INFO")


@dataclass
class EmailItem(JPickleSerializable):
    hashed_header_key:str
    header_key:str
    body_structure:List[Tuple[str]]
    email_msg:EmailMessage = field(repr=False,compare=False)

    def __init__(self,
                 hashed_header_key,
                 header_key:str,
                 body_structure:List[Tuple[str]],
                 email_msg:EmailMessage) -> None:
        super().__init__(
            "hashed_header_key",
            "header_key",
            "body_structure",
            "email_msg"
        )
        self.hashed_header_key = hashed_header_key.hexdigest()
        self.header_key = header_key
        self.body_structure = body_structure
        self.email_msg = email_msg
        self.header_hash_obj = hashed_header_key

    def __hash__(self) -> int:
        return hash(self.header_hash_obj)


class EmailDBException(DBBaseException):
    pass


class EmailDB(DBBase):

    def __init__(self,
                 db_path: Optional[Union[bytes,str,Path]] = None,
                 table_names: Optional[Union[List[str], str]] = None,
                 column_names: Optional[Union[List[str], str]] = None,
                 dtype_mapping:Dict[str,Any]=None) -> None:
        if dtype_mapping is None:
            dtype_mapping = email_datapoints_type_mapping
        if column_names is None:
            column_names = email_table_columns
        self._translation = data_point_translations
        super().__init__(db_path, table_names,column_names, dtype_mapping)

    def add_row(self, table_name:str, db_label:Optional[str]=None, curs_idx:Optional[Tuple[int]]=None,
                **column_datas:Dict[str, Any]):
        if db_label is None:
            # db_label = self._table_registry_sql_attrs.get("db_label","")
            db_label = ""
        elif db_label and not db_label.endswith("."):
            db_label += "."
        email_itm:EmailItem = column_datas["email_item"]
        email_msg:EmailMessage = email_itm.email_msg
        for col,(trans, func) in self._translation.items():
            column_datas.setdefault(col,func(email_msg.get(trans,"_Not_Available_")))
        super().add_row(table_name, db_label, curs_idx, **column_datas)

    def consolidate_mem_to_disk(self, table_names:Optional[Union[str,Union[List[str],Tuple[str]]]]=None) -> None:
        super().consolidate_mem_to_disk(table_names)
        root_con = self._con[0]
        test_curs = root_con.cursor()
        try:
            row = test_curs.execute(f"SELECT {email_table_columns[5]} FROM {self.table_names[0]};").fetchone()
            assert isinstance(row[0], EmailItem), "We aren't getting the class objects reconstructed as expected."
            info.info("All memory resident tables consolidated into disk resident tables.")
        finally:
            test_curs.close()

    def select(self, table_names: Optional[Union[str, List[str]]]=None, column_names: Optional[Union[str,List[str]]] = None,
               filters: Optional[Union[List[str], str]] = None) -> Tuple[str, Any]:
        if not table_names:
            table_names = self.table_names
        row:dict
        for tbl,row in super().select(table_names, column_names, filters):
            _row = email_table_row._make((row.get(k,None) for k in self._column_names[tbl]))
            yield tbl, _row

