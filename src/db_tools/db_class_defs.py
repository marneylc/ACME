# builtin imports
import sqlite3 as sqlt3
from typing import List, Optional, Union, Type, Tuple, Any, Dict, AnyStr
from pathlib import Path
from textwrap import dedent
from collections import ChainMap
from collections import deque
from queue import Empty

# custom code imports
from src import src_warning_logger as warn_logger
from src import DB_SUPPORTED_TYPES
from src import cache_folder
from src import to_list
from src import get_logger

info_logger = get_logger("EmailClassifier", __name__ + ": DBBase logger", level="INFO")


class DBBaseException(Exception):
    faulty_sql: List[str] = []
    faulty_db_name: List[Union[str, Path]] = []
    faulty_db_label: List[str] = []
    faulty_table: List[str] = []

    def __init__(self,
                 *args: object,
                 faulty_sql: List[str] = None,
                 faulty_db_name: List[Union[str, Path]] = None,
                 faulty_db_label: List[str] = None,
                 faulty_table: List[str] = None, ) -> None:
        super().__init__(*args)
        if faulty_sql:
            self.faulty_sql.extend(faulty_sql)
        if faulty_db_name:
            self.faulty_db_name.extend(faulty_db_name)
        if faulty_db_label:
            self.faulty_db_label.extend(faulty_db_label)
        if faulty_table:
            self.faulty_table.extend(faulty_table)


class DBConsolidationException(DBBaseException):
    pass


class AttachFailedException(DBBaseException):
    pass


class UninitializedConnectionException(DBBaseException):
    pass


class DBDetachException(DBBaseException):
    pass


class DBLockedException(DBBaseException):
    pass


class ExitException(DBBaseException):
    pass

class IllegalDBAccessException(DBBaseException):
    pass

class DBBase:
    attached_dbs:dict
    _table_names: List[str]
    _column_names: Dict[str, str]
    _con: List[sqlt3.Connection]
    _curs: List[List[sqlt3.Cursor]]
    # entry_ordinals is only updated in
    # the self.__enter__ and self.__exit__ functions
    _entry_ordinals: List[int]
    __table_attr_template__ = {
        "db_label": "main.",
        "pkey_name": "id",
        "pkey_type": DB_SUPPORTED_TYPES[int],
        "data_points": "",
    }
    _table_registry_sql_attrs: dict
    _table_mapped_column_names: dict
    _do_table_reg_context_pop: int = 0
    _do_context_detach_db: int = 0
    _uncommitted: set
    _table_registry_sql = dedent("""
    CREATE TABLE IF NOT EXISTS {db_label}{table_name} (
        {pkey_name} {pkey_type} PRIMARY KEY NOT NULL,{data_points}
    );
    """)
    # these next 7 fields are allow us to tweak the
    # default sqlite3.Connection instantiation values at the class level.
    _database: Union[bytes, str, Path]
    _timeout: float = 2.5
    _detect_types: int = sqlt3.PARSE_DECLTYPES
    _isolation_level: Optional[str] = None
    _check_same_thread: bool = True
    _factory: Type[sqlt3.Connection] = None
    _cached_statements: int = 100

    def __init__(self,
                 db_path: Optional[Union[bytes, str, Path]] = None,
                 table_names: Optional[Union[List[str], str]] = None,
                 column_names: Optional[Union[List[str], str]] = None,
                 dtype_mapping: Dict[str,Any] = None) -> None:
        self._table_registry_sql_attrs = {}
        self._table_mapped_column_names = {}
        self._table_names = []
        self._column_names = {}
        self._con = []
        self._curs = []
        self._entry_ordinals = []
        self._uncommitted = set()
        self.attached_dbs = {"label_keys": {}, "name_keys": {}}
        if db_path is None:
            db_path = Path(":memory:")
        self.database = db_path
        self._table_names.extend(to_list(table_names))
        self._column_names.update(zip(self._table_names, self._sanitize_column_names_list(column_names)))
        self.attached_dbs["label_keys"]["main."] = self.database
        self.attached_dbs["name_keys"][self.database] = "main."
        self.attached_dbs["label_keys"][""] = self.database
        self.attached_dbs["name_keys"][self.database] = ""
        table_attr_map = self._table_registry_sql_attrs
        for tname in self._table_names:
            cnames = self._column_names[tname]
            table_map = table_attr_map[tname] = ChainMap(self.__table_attr_template__.copy())
            table_map["pkey_type"] = DB_SUPPORTED_TYPES[str]
            s = ",\n    ".join(f"{n} {dtype_mapping[n]}" for n in cnames if n in dtype_mapping)
            table_map["data_points"] = f"\n\t{s}"
            table_map["table_name"] = tname
        # self._establish_new_connection(do_register_tables=False)
        self._establish_new_connection()
        # with self("main"):
        #     for table in self.table_names:
        #         self._register_table(table, self._table_registry_sql_attrs)

    def _sanitize_column_names_list(self, column_names):
        if isinstance(column_names, str):
            column_names = list(s.strip() for s in column_names.split(","))
            column_names = [column_names for _ in range(len(self._table_names))]
        elif not all(isinstance(elem, type(column_names[0])) for elem in column_names[1:]):
            # should we raise an exception if we have an ambiguous mix of types for column_names?
            # for i in range(len(column_names)):
            #     if not isinstance(column_names[i],str):
            #         column_names[i] = str(column_names[i])
            raise ValueError("column_names is a mix of different object types; "
                             "this makes it too ambiguous how we should map column names onto table names")
        elif isinstance(column_names[0], (str, bytes)):
            if isinstance(column_names[0], bytes):
                b: bytes
                for i, b in enumerate(column_names):
                    column_names[i] = b.decode("UTF-8")
            column_names = [column_names for _ in range(len(self._table_names))]
        return column_names

    @property
    def column_names(self) -> Dict[str,List[str]]:
        return self._column_names.copy()

    @property
    def table_names(self) -> List[str]:
        return self._table_names.copy()

    @property
    def database(self) -> Path:
        return Path(self._database)

    @database.setter
    def database(self, database: Union[str, bytes, Path]) -> None:
        if not isinstance(database, Path):
            database = Path(database)
        if database.stem == ":memory:":
            if database not in self.attached_dbs["name_keys"]:
                self.attached_dbs["name_keys"][database] = "memory."
                self.attached_dbs["label_keys"]["memory."] = database.stem
        elif not database.suffix == ".db":
            msg = f"\n\tThe given database name of\n\t\t{database=}"
            database = database.with_suffix(".db")
            msg += f"\n\tMust end with \".db\", so we will modify it to be:\n\t\t{database=}"
            warn_logger.warning(msg)
        self._database = database

    @property
    def connection(self) -> sqlt3.Connection:
        """Calling this property requires that we have made a previous call to self.__call__() in order to properly
        initialize our active base sqlite3.Connection.

        :return: A reference to our most recently created sqlite3.Connection object.
        :rtype: sqlite3.Connection
        """
        if not self._con:
            raise UninitializedConnectionException(
                "Exception occurred when trying to access db connection outside of proper context management.")
        return self._con[-1]

    @property
    def cursor(self) -> Tuple[sqlt3.Cursor, Tuple[int]]:
        self._curs[-1].append(self.connection.cursor())
        return self._curs[-1][-1], (len(self._curs) - 1, len(self._curs[-1]) - 1)

    def _add_to_keys(self, db_name: Union[str, Path], db_label: str = None) -> bool:
        if not isinstance(db_name, Path):
            db_name = Path(db_name)
        if db_name not in self.attached_dbs["name_keys"]:
            if db_label is not None and db_label not in self.attached_dbs["label_keys"]:
                self.attached_dbs["name_keys"][db_name] = db_label
                self.attached_dbs["label_keys"][db_label] = db_name
                return True
        return False

    def __del__(self):
        for curses in self._curs:
            for curs in curses:
                curs.close()
        if self._con:
            main_con = self._con.pop(0)
            main_con.commit()
            labels = tuple(set(self.attached_dbs["label_keys"].keys()))
            for con in self._con:
                con.commit()
                for label in labels:
                    # if self.attached_dbs["label_keys"][label]!=self.database:
                    curs = con.cursor()
                    try:
                        curs.execute(f"DETACH DATABASE '{label}';")
                    finally:
                        curs.close()
                        con.commit()
            for label in labels:
                if self.attached_dbs["label_keys"][label]!=self.database:
                    curs = main_con.cursor()
                    try:
                        curs.execute(f"DETACH DATABASE '{label}';")
                    except sqlt3.OperationalError as oe:
                        if "no such database: " not in str(oe):
                            raise oe
                    finally:
                        curs.close()
            main_con.commit()

    def commit(self) -> None:
        """Call con.commit() for all active connections that has yet uncommitted changes.

        :return: None
        :rtype: None
        """
        con: sqlt3.Connection
        while self._uncommitted:
            con = self._uncommitted.pop()
            if con.in_transaction:
                con.commit()

    def consolidate_mem_to_disk(self, table_names: Optional[Union[str, Union[List[str], Tuple[str]]]] = None) -> None:
        self.commit()
        root_con = self._con[0]
        root_con.commit()
        root_curs = root_con.cursor()
        create_table = "CREATE TABLE"
        create_len = len(create_table)
        create_guard = " IF NOT EXISTS"
        insert_into = "INSERT"
        insert_len = len(insert_into)
        insert_guard = " OR IGNORE"
        try:
            # get_tables_sql = "SELECT name,sql FROM sqlite_master WHERE type='table'"
            for tmp in self._con[1:]:
                tmp.commit()
                dump = tmp.iterdump()
                for sql in dump:
                    if sql.startswith(create_table):
                        sql = sql[:create_len] + create_guard + sql[create_len:]
                    elif sql.startswith(insert_into):
                        sql = sql[:insert_len] + insert_guard + sql[insert_len:]
                    elif sql.startswith("BEGIN") or sql.startswith("COMMIT"):
                        continue
                    root_curs.execute(sql)
                root_con.commit()
        finally:
            root_curs.close()
            root_con.commit()

    def _establish_new_connection(self, database=None, timeout=None, detect_types=None,
                                  isolation_level=None, check_same_thread=None,
                                  factory=None, cached_statements=None, do_register_tables:bool=True):
        kwargs = {name: arg
                  for arg, name in ((database if database is not None else self._database, "database"),
                                    (timeout if timeout is not None else self._timeout, "timeout"),
                                    (detect_types if detect_types is not None else self._detect_types, "detect_types"),
                                    (isolation_level if isolation_level is not None else self._isolation_level, "isolation_level"),
                                    (check_same_thread if check_same_thread is not None else self._check_same_thread, "check_same_thread"),
                                    (factory if factory is not None else self._factory, "factory"),
                                    (cached_statements if cached_statements is not None else self._cached_statements, "cached_statements"))
                  if arg is not None
                  }
        self._con.append(sqlt3.connect(**kwargs))
        self._curs.append([])  # maintains separate cursor lists for each connection
        if do_register_tables:
            for table in self.table_names:
                self._register_table(self._table_registry_sql_attrs[table])

    def __call__(self,
                 db_label: Optional[str] = None,
                 database: Optional[Union[bytes, str, Path]] = None,
                 timeout: Optional[float] = None,
                 detect_types: Optional[int] = None,
                 isolation_level: Optional[str] = None,
                 check_same_thread: bool = None,
                 factory: Optional[Type[sqlt3.Connection]] = None,
                 cached_statements: Optional[int] = None):
        """Allows us to specific instantiation arguments for each new connection we create when the caller uses
        with-blocks.

        This allows the user to create only a single instance of this database manager object and then create multiple
        nested contexts that can each add another database reference for us to connect to.

        :param db_label: A string representing the shorthand name to the database we will be connecting to
        :type db_label:
        :param database: OPTIONAL;
        :type database:
        :param timeout: OPTIONAL;
        :type timeout:
        :param detect_types: OPTIONAL;
        :type detect_types:
        :param isolation_level: OPTIONAL;
        :type isolation_level:
        :param check_same_thread: OPTIONAL;
        :type check_same_thread:
        :param factory: OPTIONAL;
        :type factory:
        :param cached_statements:
        :type cached_statements:
        :return:
        :rtype:
        """
        _database = str(database)
        if isinstance(database, bytes):
            database = database.decode("utf-8")
        database = Path(self._database if database is None else database)
        if database.stem != ":memory:":
            if not database.is_absolute():
                database = cache_folder.joinpath(database.name)
        if db_label:
            if not db_label.endswith("."):
                db_label += "."
        elif database not in self.attached_dbs["name_keys"]:
            db_label = database.stem.strip(":") + "."
        else:
            db_label = self.attached_dbs["name_keys"][database]
        # if (db_label and db_label not in self.attached_dbs["label_keys"]) or database not in self.attached_dbs["name_keys"]:
        if self._add_to_keys(database, db_label) or not self._con:
            if not self._con:
                self._establish_new_connection(database, timeout, detect_types, isolation_level,
                                               check_same_thread, factory, cached_statements)
                self._entry_ordinals.append(len(self._con) - 1)
            elif db_label:
                curs = self.connection.cursor()
                try:
                    curs.execute(f"ATTACH DATABASE '{database}' AS '{db_label.rstrip('.')}';")
                    self.connection.commit()
                finally:
                    curs.close()
            if db_label:
                db_str = str(database)
                if db_str==str(self.database) or db_str==":memory:" :
                    for tname in self._table_names:
                        # "db_label": db_label
                        self._table_registry_sql_attrs[tname].maps.insert(0,{"db_label":db_label})
                    self._do_table_reg_context_pop += 1
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            _con_idx = self._entry_ordinals.pop()
            con = self._con.pop(_con_idx)
            try:
                try:
                    curses = self._curs.pop(_con_idx)
                    for curs in curses:
                        curs.close()
                except IndexError:
                    pass
                if self._do_table_reg_context_pop:
                    self._do_table_reg_context_pop -= 1
                    for tname in self._table_names:
                        self._table_registry_sql_attrs[tname].maps.pop(0)
                con.commit()
            except sqlt3.OperationalError as e:
                if e.args[0] == "database is locked":
                    err = None
                    for i in range(10):
                        warn_logger.warning(f"Attempt number {i} to perform commit on db {con}")
                        try:
                            con.commit()
                            break
                        except sqlt3.OperationalError as oe:
                            if oe.args[0] == "database is locked":
                                pass
                            else:
                                err = ExitException(
                                    f"\n\tException occurred while trying to consolidate data to main db..."
                                    f"\n\tno sql: con.commit()"
                                    f"\n\tconnection's index: {_con_idx}"
                                    f"\nExitException raised from:"
                                    f"\n\t{type(oe)}: {oe.args}")
                        except sqlt3.Error as ee:
                            err = ExitException(f"\n\tException occurred while trying to consolidate data to main db..."
                                                f"\n\tno sql: con.commit()"
                                                f"\n\tconnection's index: {_con_idx}"
                                                f"\nExitException raised from:"
                                                f"\n\t{type(ee)}: {ee.args}")
                    else:
                        err = ExitException(f"\n\tException occurred while trying to consolidate data to main db..."
                                            f"\n\tno sql: con.commit()"
                                            f"\n\tconnection's index: {_con_idx}"
                                            f"\nExitException raised from:"
                                            f"\n\t{type(e)}: {e.args}")

                else:
                    err = ExitException(f"\n\tException occurred while trying to consolidate data to main db..."
                                        f"\n\tno sql: con.commit()"
                                        f"\n\tconnection's index: {_con_idx}"
                                        f"\nExitException raised from:"
                                        f"\n\t{type(e)}: {e.args}")
                if err is not None:
                    raise err from e
            except sqlt3.Error as e:
                err = ExitException(f"\n\tException occurred while trying to consolidate data to main db..."
                                    f"\n\tno sql: con.commit()"
                                    f"\n\tconnection's index: {_con_idx}"
                                    f"\nExitException raised from:"
                                    f"\n\t{type(e)}: {e.args}")
                raise err from e
            finally:
                con.close()
            self._uncommitted.discard(con)
        except IndexError:
            pass

    def _register_table(self, attrs_dict: dict,
                        con: Optional[sqlt3.Connection] = None,
                        curs: Optional[sqlt3.Cursor] = None):
        exec_sql = self._table_registry_sql.format(**attrs_dict)
        if curs is None:
            if con is None:
                con = self.connection
            curs = con.cursor()
            try:
                curs.execute(exec_sql)
            except sqlt3.OperationalError as oe:
                raise oe
            except BaseException as be:
                raise be
            finally:
                curs.close()
        else:
            if con is None:
                con = curs.connection
            curs.execute(exec_sql)
        self._uncommitted.add(con)

    def _register_index(self):
        pass

    def select(self,
               table_names: Optional[Union[str, List[str]]],
               column_names: Optional[Union[str, List[str]]] = None,
               filters: Optional[Union[List[str], str]] = None) -> Tuple[str, Any]:
        """This is a generator function that will extract all rows in the requested table(s), and expose the data in
        the optionally defined columns, using the optionally defined filters.

        The resulting SQLite statement will look something like this:
        ::
            SELECT
                column_list
            FROM
                table
            WHERE
                search_condition;

        Note:
            1)
                The table_names argument will be filtered against the table names actually present in the main database.
                If a table name found in table_names does not exist in the main database for this DBBase object, then it
                will be ignored and any filters associated with that table name will also be ignored.

            2)
                The filters argument must be submitted as a valid sql WHERE statement.
                Consider the following separate examples; the names used, `column_x`, are contrived examples.
                Your string must use your table's valid column names.

                If you provide a list of strings, we assume that each string in filters that starts with `WHERE` is an
                independent and should be paired with the table name of the same list position in the table_names. All
                strings in the filters list that do not start with `WHERE` are assumed to be part of the first previous
                list element that started with `WHERE`. We assume the first element of the filters list must start with
                `WHERE` and will prepend to that string otherwise.

                if table_names is given as a single string, then we will only use the first where statement from
                the given list of filters.
            ::

                - WHERE column_1 = 100;
                - WHERE column_2 IN (1,2,3);
                - WHERE column_3 LIKE 'An%';
                - WHERE column_4 BETWEEN 10 AND 20;
                - WHERE column_1 = 100 OR column_2 IN (1,2,3);
                - WHERE column_3 LIKE 'An%' AND column_4 BETWEEN 10 AND 20;

        :param table_names: A string, or a list of strings, giving the table names we should query in this select.
        :type table_names: Union[str, List[str]]

        :param column_names: An optional string, or list of strings, that give the names of the columns we should
                             retrieve from the table(s) given in table_names.
        :type column_names: Union[str, List[str]]

        :param filters: An optional string, or list of strings, that specify the filtering conditions we should employ
                        to restrict what data is returned.
        :type filters: Union[str, List[str]]

        :return: A 2-Tuple, where the first element is the name of the source table, and the second is the row contents
        :rtype:
        """
        table_names = to_list(table_names)
        column_names = to_list(column_names)
        filters = to_list(filters)
        curs = self.connection.cursor()
        try:
            valid_names = set(
                t[0] for t in curs.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
        finally:
            curs.close()
        table_names = [name if name in valid_names else None for name in table_names]
        if column_names is None:
            column_names = ["*"]
        elif isinstance(column_names, str):
            column_names = [list(v.strip() for v in column_names.split(","))]
        elif isinstance(column_names[0],str):
            column_names = [[v.strip() for v in s.split(",")] for s in column_names]
        if filters is None:
            filters = ["" for _ in table_names]
        elif isinstance(filters, str):
            filters = [filters]
        filters: list
        for i in range(len(filters) - 1, 0, -1):
            _filter = filters[i].lstrip().upper()
            if _filter and not _filter.startswith("WHERE"):
                filters[i - 1] += " AND " + _filter
                filters.pop(i)
        con = self.connection
        con.row_factory = sqlt3.Row
        curs = con.cursor()
        select_sql = "SELECT {columns} FROM {table}{filter};"
        try:
            for i, table in enumerate(table_names):
                if i < len(column_names):
                    _column_names = column_names[i]
                else:
                    _column_names = ["*"]

                column_names_str = ", ".join(_column_names)
                if i < len(filters) and filters[i]:
                    _filter = " " + filters[i]
                else:
                    _filter = ""
                _sql = select_sql.format(columns=column_names_str, table=table, filter=_filter)
                if table is not None:
                    curs.execute(_sql)
                    batch = curs.fetchmany()
                    while batch:
                        for row in batch:
                            yield table, dict(row)
                        batch = curs.fetchmany()
        finally:
            curs.close()

    def add_row(self, table_name: str, db_label: str, curs_idx: tuple = None, **row_obj: dict):
        drop_cursor = curs_idx is None
        if drop_cursor:
            curs = self.connection.cursor()
            con = None
        else:
            curs = self._curs[curs_idx[0]][curs_idx[1]]
            con = self._con[curs_idx[0]]
        try:
            if not drop_cursor and len(curs_idx) == 1:
                _ = self._curs[curs_idx[0]].append(self._con[curs_idx[0]].cursor())
                curs_idx += len(self._curs[curs_idx[0]]) - 1,
            if db_label and not db_label.endswith("."):
                db_label += "."
            column_labels = tuple(row_obj.keys())
            # column_labels = "id",
            datas = tuple(row_obj[k] for k in column_labels)
            insertion_sql = f"INSERT INTO {db_label}{table_name}" \
                            f"({','.join(str(l) for l in column_labels)})" \
                            f"\nVALUES({','.join('?' for _ in datas)});"
            curs.execute(insertion_sql,datas)
            if not drop_cursor:
                self._uncommitted.add(con)
        finally:
            if drop_cursor:
                curs.close()

class ThreadedDBBase(DBBase):
    _exec_queue: deque
    _producers: set

    def __init__(self, db_name: Optional[Union[bytes, str, Path]] = None,
                 table_names: Optional[Union[List[str], str]] = None,
                 column_names: Optional[Union[List[str], str]] = None) -> None:
        super().__init__(db_name, table_names, column_names)

        self._exec_queue = None
        self._thread_processor = None

    def __next__(self):
        if self._thread_processor is not None:
            try:
                return next(self._thread_processor)
            except GeneratorExit or StopIteration:
                return False
        return False

    def __call__(self, db_label: Optional[str] = None, attachables: Optional[List[Tuple[Union[str, Path], str]]] = None,
                 database: Optional[Union[bytes, str, Path]] = None, timeout: Optional[float] = None,
                 detect_types: Optional[int] = None, isolation_level: Optional[str] = None,
                 check_same_thread: bool = None, factory: Optional[Type[sqlt3.Connection]] = None,
                 cached_statements: Optional[int] = None, q: deque = None):
        super().__call__(db_label, attachables, database, timeout, detect_types, isolation_level,
                         check_same_thread, factory, cached_statements)
        if q is not None and self._exec_queue is None:
            self._exec_queue = q
            self._producers = set()
            self._thread_processor = self._threaded_consumer()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        if not self._con:
            self.signal_queue_close()

    def str2func(self, func_name: str):
        if func_name:
            if not func_name.startswith("_"):
                func_name = "_" + func_name
            return getattr(self, func_name, lambda **_: None)
        return lambda **_: None

    def _threaded_consumer(self):
        non_signaled = False
        while self._producers or not non_signaled:
            # info_logger.warning(f"{len(command)=}")
            while not self._exec_queue:
                yield True
            command: Optional[Dict[str, Any]] = self._exec_queue.popleft()
            if command is not None:
                func = self.str2func(command.pop("func", ""))
                info_logger.info(f"{func.__name__}")
                func(**command)
            else:
                non_signaled = True
        self._exec_queue = None
        self._producers = None
        yield False

    def signal_queue_close(self):
        if self._exec_queue is not None:
            self._exec_queue.append(None)

    def enqueue_add_producer(self, producer_id: str):
        if self._exec_queue is not None:
            self._exec_queue.append(dict(func=self._add_producer, producer_id=producer_id))
        else:
            warn_logger.warning(
                "Warning, called enqueue_add_producer before establishing self._exec_queue = JoinableQueue()")

    def _add_producer(self, producer_id: str):
        self._producers.add(producer_id)

    def enqueue_drop_producer(self, producer_id: str, success: bool = False):
        if self._exec_queue is not None:
            self._exec_queue.append(dict(func=self._drop_producer, producer_id=producer_id, success=success))
        else:
            warn_logger.warning(
                "Warning, called enqueue_add_producer before establishing self._exec_queue = JoinableQueue()")
        return producer_id

    def _drop_producer(self, producer_id: str, success: bool):
        if success:
            info_logger.info(f"{producer_id} added a row to the db")
        self._producers.remove(producer_id)

    def enqueue_add_row(self, table_name: str, db_label: str, curs_idx: tuple = None, **row_obj: dict):
        if self._exec_queue is not None:
            self._exec_queue.append(
                dict(func=self.add_row, table_name=table_name, db_label=db_label, curs_idx=curs_idx, **row_obj))
        else:
            warn_logger.warning(
                "Warning, called enqueue_add_row before establishing self._exec_queue = JoinableQueue()")
