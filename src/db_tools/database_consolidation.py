from pathlib import Path
from typing import Optional, Union, List, Dict, Any
import sqlite3 as sqlt3

from src import TABLE_NAMES
from src.eralchemy.main import render_er


def doit_consolidate_databases(targets:List[str], file_dep:List[str]):
    consolidate_databases(Path(targets[0]), {p.stem:p for p in (Path(f) for f in file_dep)})


def consolidate_databases(consolidated_db_path:Path, satalite_databases:Dict[str,Path]):
    satalite_labels = []
    with sqlt3.connect(consolidated_db_path) as conn:
        conn.row_factory = sqlt3.Row
        try:
            for k,v in satalite_databases.items():
                if k.startswith("sql3_"):
                    k = k[k.rfind("_")+1:]
                satalite_labels.append(k)
                tables = TABLE_NAMES[k]
                conn.execute(f"ATTACH DATABASE '{v}' as '{k}'")
                curs = conn.cursor()
                try:
                    for tbl in tables:
                        curs.execute(f"SELECT name,sql FROM '{k}'.sqlite_master AS sqm WHERE sqm.type='table' AND sqm.name=?",(tbl,))
                        curs2 = conn.cursor()
                        try:
                            row:sqlt3.Row
                            for row in tuple(curs.fetchall()):
                                name = row['name']
                                sql = row['sql']
                                curs3 = conn.cursor()
                                table_row:sqlt3.Row = curs3.execute(f"SELECT * from '{k}'.{name}").fetchone()
                                pkey,*_ = tuple(table_row.keys())
                                curs3.close()
                                start = sql.find(name)-1
                                exec_sql =  sql[:start]+" IF NOT EXISTS "+sql[start:] + ";"
                                exec_sql += f"\nINSERT INTO main.{name} SELECT * FROM '{k}'.{name} WHERE NOT EXISTS(SELECT {pkey} FROM main.{name});"
                                print(exec_sql)
                                curs2.executescript(exec_sql)
                            conn.commit()
                            dbg_break = 0
                        finally:
                            curs2.close()
                finally:
                    curs.close()
            conn.commit()
        finally:
            for k in satalite_labels:
                conn.execute(f"DETACH DATABASE '{k}'")
            conn.commit()
        conn.executescript("""
-- Creating the unified ROWID table that maps the unique id shared by all tables
-- to the respective ROWID for a given table, where each column name is the name
-- of one of our tables.
drop table if exists all_tables_by_id;
create table all_tables_by_id(
id text primary key not null,
email text not null,
message_body text not null,
all_lemma text not null,
no_stopwords_lemma text not null,
foreign key (email) references emails(id),
foreign key (message_body) references message_body(id),
foreign key (all_lemma) references all_lemma(id),
foreign key (no_stopwords_lemma) references no_stopwords_lemma(id)
);
insert into all_tables_by_id
select
       e.id as id,
       e.id as email,
       mb.id as message_body,
       al.id as all_lemma,
       nsl.id as no_stopwords_lemma
from
     emails e
left join
         all_lemma al on e.id=al.id
left join
         message_body mb on e.id=mb.id
left join
         no_stopwords_lemma nsl on e.id=nsl.id;

-- Create the index for looking up ROWIDs  for a given object id
drop index if exists index_all_tables_by_id;
create unique index index_all_tables_by_id
on all_tables_by_id(id);
        """)


def doit_generate_erd(targets:List[str], file_dep:List[str])->None:
        targets = [str(Path(t).resolve()) for t in targets]
        db_path = f"sqlite+pysqlite:///{Path(file_dep[0]).resolve()}"
        render_er(db_path,targets)


if __name__ == '__main__':
    from src import DB_PATH_DICT
    _target = Path(__file__).resolve().parent
    itr = _target.parts
    for i,part in enumerate(itr):
        if part == "EmailClassification":
            _target = Path("/".join(itr[:i+1])).joinpath("cache_files\\db_diagrams")
    _target.mkdir(parents=True,exist_ok=True)
    consolidate_databases(DB_PATH_DICT["consolidated"], {p.stem:p for p in DB_PATH_DICT.values() if "consolidated" not in p.stem})
    doit_generate_erd([str(_target.joinpath("central_db.png")),str(_target.joinpath("central_db.er"))], [str(DB_PATH_DICT["consolidated"])])
    for target_label in ("email","body","lemma"):
        doit_generate_erd([str(_target.joinpath(f"{target_label}_db.png")), str(_target.joinpath(f"{target_label}_db.er"))],[str(DB_PATH_DICT[target_label])])