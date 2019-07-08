from _mysql_exceptions import OperationalError
import os ,pymysql,re
import cPickle as pickle
# from nltk import MaxentClassifier
from Communicator import Communicator
from Config import Config
from corpus import CORPUS
from databasefile import Database , NodeType , Node ,SchemaGraph
from Classifiers import SQLGrammarClassifier ,DBSchemaClassifier ,DBCorpusClassifier ,DBCorpusGenerator

"""
Files Paths 
"""

graph_path = 'data/graph.p'
corpus_path = 'data/database_corpus.p'
stanford_jar = 'data/stanford-corenlp-full-2016-10-31/stanford-corenlp-3.7.0.jar'

"""
Models Paths 
"""

sql_model_path = 'data/sql_model.p'
db_model_path =  'data/db_model.p'


"""
Creating a DB Graph consisting of all the table mappings of the database
"""
def create_db_graph():
    comm.say("Constructing Database Graph.")
    try:
        database = Database()
    except ValueError as exception:
        comm.error("Error: %s" % exception)

    #Constructing the Graph and storing in graph.p file
    SchemaGraph().construct(database, graph_path)

    comm.say("Database Graph constructed.")

"""
A corpus is a collection of text documents #Assigning tags/tokens to all the database table values
"""
def create_db_corpus():
    comm.say("Creating Database Corpus.")
    # tokenizer = StanfordTokenizer(jar_path)
    try:
        database = Database()
    except ValueError as exception:
        comm.error("Error: %s" % exception)

    #Calling class for assigning attributes their respective tags
    gen = DBCorpusGenerator(stanford_jar)
    gen.create_db_corpus(database, corpus_path)
    comm.say("Database Corpus created.")

"""
Training the complete database using classifier
"""
def train_db_classifier():

    comm.say("Training database classifier.")
    DBCorpusClassifier().train(corpus_path, db_model_path)    
    comm.say("Database classifier trained.")

"""
Training for SQL Queries using the grammar in corpus.py file
"""
def train_sql_classifier():
    comm.say("Training SQL grammar classifier.")

    SQLGrammarClassifier().train(sql_model_path)
    comm.say("SQL grammar classifier trained.")


if __name__ == '__main__':
  
    #Initialize the Communicatior
    comm = Communicator()
    #Check for the path in Configuration file.
    comm.say("Setting up the Training Environment.")
    #Creating a DB Graph consisting of all the table mappings of the database
    create_db_graph()
    #Assigning tags/tokens to all the database table values
    create_db_corpus()
    #Training the complete database using classifier
    train_db_classifier()
    #Training for SQL Queries using the grammar in corpus.py file
    train_sql_classifier()
    comm.say("Set up complete.")