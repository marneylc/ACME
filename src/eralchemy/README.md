IMPORTANT NOTE:
===
## Original source of this submodule: 
[eralchemy](https://github.com/Alexis-benoist/eralchemy)

### Explanation:
This submodule of the project was copied and slightly modified from its original source to work in a virtual environment running `python >= 3.8`.
This is a very crude but quick band-aid fix that allowed the project to programmatically generate rudimentary Entity Relationship Diagram (ERD) from the [Sqlite](https://www.sqlite.org/index.html) database structures used to cache persistent data used in this project. 

### A list of changes made for use in this project:

1) A a result of the somewhat sloppy process by which the code was included in this project, the following files saw changes to how they performed relative imports from other `eralchemy` project files.
   ```python
   ~\EmailClassification\src\eralchemy\main.py
       line number: 9;                          from eralchemy.version import version as __version__
                            changed to:         from src.eralchemy.version import version as __version__
   
       line number: 10;                         from eralchemy.cst import GRAPH_BEGINNING
                            changed to:         from src.eralchemy.cst import GRAPH_BEGINNING
   
       line number: 11;                         from eralchemy.sqla import metadata_to_intermediary, declarative_to_intermediary, database_to_intermediary
                            changed to:         from src.eralchemy.sqla import metadata_to_intermediary, declarative_to_intermediary, database_to_intermediary
   
       line number: 12;                         from eralchemy.helpers import check_args
                            changed to:         from src.eralchemy.helpers import check_args
   
       line number: 13;                         from eralchemy.parser import markdown_file_to_intermediary, line_iterator_to_intermediary, ParsingException
                            changed to:         from src.eralchemy.parser import markdown_file_to_intermediary, line_iterator_to_intermediary, ParsingException
   
   
   ~\EmailClassification\src\eralchemy\models.py
       line number: 1;                          from eralchemy.cst import TABLE, FONT_TAGS, ROW_TAGS
                            changed to:         from src.eralchemy.cst import TABLE, FONT_TAGS, ROW_TAGS
   
   ~\EmailClassification\src\eralchemy\parser.py
       line number: 1;                          from eralchemy.models import Table, Relation, Column
                            changed to:         from src.eralchemy.models import Table, Relation, Column
   
   ~\EmailClassification\src\eralchemy\sqla.py
       line number: 5;                          from eralchemy.models import Relation, Column, Table  
                            changed to:         from src.eralchemy.models import Relation, Column, Table
   
   ```
2) `Eralchemy` is built to operate with both conventional `Sqlite` database objects and special OOP generated relational databases built from the `sqlalchemy` python package. 
   
   As such, there have been changes introduced in the past 3 years to `sqlalchemy` which broke certain interactions with `eralchemy`. The fixes for those follow:
   1) In the file, `~\EmailClassification\src\eralchemy\sqla.py` starting on line number 46;
   ```python
   # original version:
   # This implementation broke because one of the base classes to the table object,
   # ImmutableColumnCollection from sqlalchemy, no longer provides the _data property.
   def table_to_intermediary(table):
      """Transform an SQLAlchemy Table object to it's intermediary representation. """
      return Table(
         name=table.fullname,
         columns=[column_to_intermediary(col) for col in table.c._data.values()]
      )
   
   # fixed version:
   # we now perform a sanity check if the `_data` property exists, if it doesn't then we know
   # we should use the `_colset` property instead.
   def table_to_intermediary(table):
      """Transform an SQLAlchemy Table object to it's intermediary representation. """
      return Table(
          name=table.fullname,
          columns=[column_to_intermediary(col) 
                   for col in (table.c._data.values() 
                               if hasattr(table.c,"_data") else table.c._colset)]
      )
   ```