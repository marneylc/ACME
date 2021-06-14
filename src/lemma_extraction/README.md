# Lemma extraction sub-module (/src/lemma_extraction/)

This module is responsible for performing preliminary data extraction for statistical analysis.

The module requires that there exists a SQLite database with a path defined in the DB_PATH_DICT under the key `body_cache` (or simply `body`)
that contains the table `message_body`. 

The `message_body` table must include the column `processed_body` which we will use as our data source for each email message.
