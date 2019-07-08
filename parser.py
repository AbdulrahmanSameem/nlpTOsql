from nltk.parse.stanford import StanfordParser, StanfordDependencyParser
from nltk.tree import ParentedTree

"""
Parse sentence structure
"""
class Parser(object):

    def __init__(self, jar_path, model_path):
        self.parser = StanfordParser(jar_path, model_path)
        self.dep_parser = StanfordDependencyParser(jar_path, model_path)


    def __call__(self, doc):
        doc['parse'] = ParentedTree.convert(self.parse(doc['text']))
        doc['dep_parse'] = self.dep_parse(doc['text'])


    def parse(self, statement):
        return next(self.parser.raw_parse(statement))


    # (raw_parse) Use StanfordParser to parse a sentence. Takes a sentence as a string;
    # before parsing, it will be automatically tokenized and tagged by
    # the Stanford Parser.

    def dep_parse(self, statement):
        return next(self.dep_parser.raw_parse(statement))
