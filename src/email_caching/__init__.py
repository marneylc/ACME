from collections import namedtuple

from src import DB_SUPPORTED_TYPES

email_table_columns = "id","recipient", "sender", "subject", "received", "email_item", "ref_ids"
email_table_row = namedtuple("EmailTableRow",email_table_columns)

# data_point_translations is specifically meant to map the meta-data contained in imap email header to our table columns.
# We change some names from how they appear in the imap header to avoid reserved keywords in sqlite scripting.
# A quick note about the "ref_ids" column label:
#   if a given message is the culmination of a chain of messages, then those previous messages are considered to be
#   references for this message. We create a specific column for those ids in case we want to later implement some sort
#   of indexing for fast lookups on those references.
data_point_translations = {"recipient":("To",str), # to is reserved in sqlite
                           "sender":("From",str),  # from is reserved in sqlite
                           "subject":("Subject",str),
                           "received":("Recieved",str),
                           "id":("Message-ID",lambda v:str(v).strip()),
                           "ref_ids":("References",str)
                           }
email_datapoints_type_mapping = {
    "recipient": DB_SUPPORTED_TYPES[str],
    "sender": DB_SUPPORTED_TYPES[str],
    "subject": DB_SUPPORTED_TYPES[str],
    "received": DB_SUPPORTED_TYPES[str],
    "email_item": DB_SUPPORTED_TYPES['custom_cls'],
    "ref_ids": DB_SUPPORTED_TYPES[str]
}
