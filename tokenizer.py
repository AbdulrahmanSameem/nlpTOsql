from nltk.tokenize import word_tokenize
from Communicator import Communicator

def make_doc(statement):
    return {
        'text': statement,
        'tokens': word_tokenize(statement),
        'tagged': {}
    }
def print_details(sql):

    comm = Communicator()

    comm.say("SQL: %s" % sql)

