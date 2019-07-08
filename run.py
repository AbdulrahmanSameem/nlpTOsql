#Personal Imports
from tokenizer import make_doc ,print_details
from parser import Parser
from Communicator import Communicator
from corpus import CORPUS
from sql import NodeGenerator, SQLGenerator
from databasefile import Database , NodeType , Node ,SchemaGraph
from Classifiers import SQLGrammarClassifier ,DBSchemaClassifier ,DBCorpusClassifier
from nltk import word_tokenize

import spacy
import re
import nltk
from nltk import chunk
from spacy import displacy

if __name__ == '__main__':

    comm = Communicator()

    """
    Files Paths 
    """
    
    graph_path = 'data/graph.p'
    stanford_jar = 'data/stanford-corenlp-full-2018-10-05/stanford-corenlp-3.9.2.jar'
    stanford_models_jar = 'data/stanford-corenlp-full-2018-10-05/stanford-corenlp-3.9.2-models.jar'
    
    """
    Models Paths 
    """
    sql_model_path = 'data/sql_model.p'
    db_model_path =  'data/db_model.p'

    schema_graph = SchemaGraph(graph_path)
    parser = Parser(stanford_jar , stanford_models_jar)
    # tags()->[(u'show', 'SELECT'), (u'all', 'IGN'), (u'customers', 'UNK')]
    grammar_classifier = SQLGrammarClassifier(sql_model_path)
    # [(u'customers', [('customer', 1.0), ('customer.customer_id', 0.8528028654224418)])]
    schema_classifier = DBSchemaClassifier(schema_graph)

    corpus_classifier = DBCorpusClassifier(db_model_path)
    pipeline = [parser, grammar_classifier, schema_classifier, corpus_classifier]

    node_generator = NodeGenerator(comm)    
    comm.greet()

    while True:

        statement = raw_input("  >>> ") 

        if statement.lower() == "":
            continue
        if statement.lower() == 'exit':
            print ('\ngood bye !!')
            break
        if statement.lower() == 'no':
            print ('\ngood bye !!')
            break
        tagged = nltk.pos_tag(nltk.word_tokenize(statement))
        doc = make_doc(statement)
        for process in pipeline:
            process(doc)

        tree = node_generator(doc)

        sql_generator = SQLGenerator(tree, schema_graph)

        sql = sql_generator.get_sql()
        print_details(sql)
        print "test"
        
        database = Database()
        database.execute(sql, True)
    
        comm.resume()