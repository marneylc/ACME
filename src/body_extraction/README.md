# Body Extraction sub-module (/src/body_extraction/)

This module is responsible for parsing `imap` message envelop structures to extract the message text (aka message body)
and saving it as a string.

### Assumptions:
This module makes the following assumptions regarding the state of its inputs and the requirements for its output.

#### Input:
1. The `imap` envelope structure is cached to disk on a SQLite database.
   * The path to this database can be found in the DB_PATH_DICT (a global variable defined in ..utils.\_\_init__.py) under the key `'emails'`
2. The 

The module requires that there exists a SQLite database with a path defined in the DB_PATH_DICT under the key `body_cache` (or simply `body`)
that contains the table `message_body`. 

The `message_body` table must include the column `processed_body` which we will use as our data source for each email message.
