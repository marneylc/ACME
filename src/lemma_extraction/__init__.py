from collections import namedtuple

from src import DB_SUPPORTED_TYPES


lemma_columns = "id", "lemma", "joined", "counts", "csr_mat", "features"
lemma_table_row = namedtuple("LemmaTableRow", lemma_columns)
lemma_datapoints_type_mapping = {
    "lemma":DB_SUPPORTED_TYPES["simple"],  # a list of strings, so use SIMPLE_JSON
    "joined":DB_SUPPORTED_TYPES[str],      # a single string, so use TEXT
    "counts":DB_SUPPORTED_TYPES["complex"], # a dict of str(word):int(count), so use COMPLEX_JSON, see NOTE 1 at end of file
    "csr_mat":DB_SUPPORTED_TYPES["complex"], # a complicated class found at: from scipy.sparse.csr import csr_matrix
    "features":DB_SUPPORTED_TYPES["simple"], # a list of strings, so use SIMPLE_JSON
}

# NOTE 1:
#   Regarding specifying a simple dict of (str,int) mappings as COMPLEX_JSON.
#       We have no way to know how complicated the potentially nested structures within a given dictionary can be without
#       manually exploring it when we wish to add the dict to our database. So we are opting to use the most robust
#       solution available, and we are encoding it to a json string using the complex json adapter defined in the
#       project's root __main__.py file.
