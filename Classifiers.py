from corpus import CORPUS
from sql import NodeGenerator, SQLGenerator
import cPickle as pickle
import re 
from nltk import NaiveBayesClassifier,word_tokenize,MaxentClassifier
from nltk import UnigramTagger, DefaultTagger,BigramTagger
import nltk
from nltk.corpus import wordnet
from nltk.metrics import jaccard_distance
from math import sqrt

class SQLGrammarClassifier(object):
    def __init__(self, model_path=None):
        if model_path:
            with open(model_path, "rb") as model_file:
                self.tagger = pickle.load(model_file)


    def __call__(self, doc):
        tokens = [token.lower() for token in doc['tokens'] if token not in doc['tagged']]

        tags = self.classify(tokens)
        # tags()->[(u'show', 'SELECT'), (u'all', 'IGN'), (u'customers', 'UNK')]
        for index, token in enumerate(doc['tokens']):
            if tags[index][1] == 'UNK':
                continue

            doc['tagged'][doc['tokens'][index]] = {
                'type': 'grammar',
                'tags': tags[index][1]
            }

    def classify(self, tokens):
        return self.tagger.tag(tokens)

    def train(self, model_path):
        corpus = [[(token.lower(), tag) for token, tag in sent] for sent in CORPUS]
        # print corpus
        unigram_tagger = UnigramTagger(corpus, backoff=DefaultTagger('UNK'))
        bigram_tagger = BigramTagger(corpus, backoff=unigram_tagger)

        with open(model_path, "wb") as model_file:
            pickle.dump(bigram_tagger, model_file)

"""
Find tokens that are similiar to database tables or column names
"""
class DBSchemaClassifier(object):

    def __init__(self, schema_graph):
        self.nodes = [schema_graph.get_node(label) for label in schema_graph.nodes()]

    def __call__(self, doc):
        trees = [tree.leaves() for tree in doc['parse'].subtrees(self.filter_tree)]
        # print trees
        tokens = [token for leaves in trees for token in leaves if token not in doc['tagged']]
        matches = [match for match in self.find_db_matches(tokens) if match[1]]

        # print matches

        for match in matches:
            doc['tagged'][match[0]] = {
                'type': 'schema',
                'tags': match[1]
            }
    
    def find_db_matches(self, tokens, cutoff=.8, table=''):
        nodes = [node for node in self.nodes if node.label.startswith(table)]
        matches = [] 
        for word in tokens:
            matches.append((word, self.most_sim_node(word, cutoff, nodes)))
            # print word
        return matches


    def most_sim_node(self, word, cutoff, nodes):
        matches = []
        TABLE = 1
        # reading all db nodes (table and its attribute)
        for node in nodes:
            name = node.table if node.type == TABLE else node.attribute
            # print name 

            # name customer word u'customer'
            sim = self.similarity(word, name)

            if sim >= cutoff:
                matches.append((node.label, sim))

        return matches
        # sorted(matches, key=lambda x: x[1], reverse=True)

    @staticmethod
    def similarity(word1, word2):
        wup = wup_sim(word1, word2)
        jaccard = jaccard_sim(word1, word2)
        # print wup , sqrt(jaccard)
        # print max(wup, sqrt(jaccard))
        return max(wup, sqrt(jaccard))

    @staticmethod
    def filter_tree(tree):
        """
        Filters parse tree to Nouns located in Noun Phrases
        May need to expand or remove this filter
        """
        return find_noun(tree)

        # noun_phrase = re.match("NP|WHNP", tree.parent().label())
        # noun = re.match("NN.*", tree.label())
        # return noun_phrase and noun

def find_noun(tree):

    if tree.parent() is None:
        return False

    noun = []    
    for s in tree.subtrees(lambda tree: tree.label() in ['S','NP']):
        for n in s.subtrees(lambda n: n.label().startswith('NN')):
            noun.append(n[0])
        return(noun)


def find_pos(tree):

    if tree.parent() is None:
        return False

    noun_phrase = re.match("NP|VP", tree.parent().label())
    pos = re.match("NN.*|JJ|CD|VBN", tree.label())
    return noun_phrase and pos



def wup_sim(word1, word2):
    # if word2 == "id":
    #     return 0

    synset1 = wordnet.synsets(word1)
    synset2 = wordnet.synsets(word2)

    if not synset1 or not synset2:
        return 0

    if synset1[0] == synset2[0]:
        return 1.0

    return wordnet.wup_similarity(synset1[0], synset2[0])

def jaccard_sim(word1, word2):
    set1 = set(word1)
    set2 = set(word2)
    coefficient = 1 - jaccard_distance(set1, set2)
    return coefficient

"""
Classify tokens based on values in the database
"""
class DBCorpusClassifier(object):

    def __init__(self, model_path=None):
        if model_path:
            with open(model_path, "rb") as model_file:
                self.classifier = pickle.load(model_file)

    def __call__(self, doc):
        trees = [tree.leaves() for tree in doc['parse'].subtrees(self.filter_tree)]
        tokens = [token for leaves in trees for token in leaves if token not in doc['tagged']]

        tags = self.classify(tokens)
        # for taf in tags:
        #     print taf
        for tag in tags:
            doc['tagged'][tag[0]] = {
                'type': 'corpus',
                'tags': tag[1]
            }
    def shape(self, word):
        if re.match(r'@', word, re.UNICODE):
            return 'email'
    
        if re.match(r'[0-9]+(\.[0-9]*)?|[0-9]*\.[0-9]+$', word, re.UNICODE):
            return 'number'
    
        if re.match(r'\W+$', word, re.UNICODE):
            return 'punct'
    
        if re.match(r'[a-zA-Z]+$', word, re.UNICODE):
            return 'alpha'
    
        if re.match(r'\w+$', word, re.UNICODE):
            return 'mixedchar'
    
        return 'other'

    @staticmethod
    def filter_tree(tree):
        """
        Filters parse tree to certain POS in Noun Phrases
        May need to expand or remove this filter
        """
        return find_pos(tree)

        # if tree.parent() is None:
        #     return False

        # noun_phrase = re.match("NP|VP", tree.parent().label())
        # pos = re.match("NN.*|JJ|CD|VBN", tree.label())
        # return noun_phrase and pos

    # Determin the category of the entity being regerred to 

    def classify(self   , tokens, limit=3):
        history = []
        results = []

        for i, _ in enumerate(tokens):
            feature_set = self.db_row_features(tokens, i, history)
            # print feature_set
            # prob_classify -- Returns:    a probability distribution over labels for the given featureset.
            pdist = self.classifier.prob_classify(feature_set)
            labels = sorted(pdist.samples(), key=pdist.prob, reverse=True)

            history.append(pdist.max())
            results.append([(label, pdist.prob(label)) for label in labels[:limit]])

        # (u'Farhad', [('customer.name', 0.7173913043478268), ('customer.title', 0.07971014492753623)])

        return zip(tokens, results)

    def train(self, corpus_path, model_path):
        #opening the database_corpus.p file created using DBCorpusGenerator and storing in corpus datastructure
        with open(corpus_path) as corpus_file:
            corpus = pickle.load(corpus_file)

        train_set = []
        #Iterating through the corpus DS(Data Structure)
        for row in corpus:
            #Storing value in sentence
            sentence = [value for (value, _) in row]
            history = []
            for i, (value, column) in enumerate(row):
                #Creating row features
                feature_set = self.db_row_features(sentence, i, history)
                #Adding all row features to train_set
                # print feature_set
                train_set.append((feature_set, column))
                history.append(column)
                # print history
        #Classifying all table's row features using MaxentClassifier
        classifier = NaiveBayesClassifier.train(train_set)
        # print "   ---> Naive Bayes Accuracy:", ((nltk.classify.accuracy(classifier,train_set))*100)
        # classifier = MaxentClassifier.train(train_set, max_iter=100)
        
        #Storing the classified values to db_model.p file
        # print classifier
        with open(model_path, "wb") as model_file:
            pickle.dump(classifier, model_file)


    #Adding features to the rows of the tables
    def db_row_features(self, sentence, i, history):
        word = str(sentence[i])
        word_shape = self.shape(word)

        features = {
            'token': word,
            'lower': word.lower(),
            'shape': word_shape
            }

        if i > 0:
            prev_token = str(sentence[i-1])
            features['prev_tag'] = history[i-1]
            features['prev_token'] = prev_token
            features['prev_lower'] = prev_token.lower()
            features['prev_token+token'] = "%s+%s" % (prev_token, word)
            features['prev_lower+lower'] = "%s+%s" % (prev_token.lower(), word.lower())
            features['prev_tag+token'] = "%s+%s" % (history[i-1], word)
            features['prev_tag+lower'] = "%s+%s" % (history[i-1], word.lower())
            features['prev_tag+shape'] = "%s+%s" % (history[i-1], word_shape)

        if i < len(sentence) - 1:
            next_token = str(sentence[i+1])
            features['next_token'] = next_token
            features['next_lower'] = next_token.lower()
            features['token+next_token'] = "%s+%s" % (word, next_token)
            features['lower+next_lower'] = "%s+%s" % (word.lower(), next_token.lower())

        return features

"""
Generate a corpus based on the database # for each table pair of [(value , lable )]
"""
class DBCorpusGenerator(object):

    def __init__(self, jar_path):
        pass
        # tokenizer = StanfordTokenizer(jar_path)

    def create_db_corpus(self, database, path):
        #Defining all tables and the attributes of the those tables to be used
        tables = {
            'employee':['enumber','ename','job','manager','hiredate','salary','commission','dnumber'],
            'department':['dnumber','dname','location']
#            'customer':['title','name','address','town','phone','zipcode'],
 #           'orderinfo':['order_id','details','date_placed','date_shipped','salary'],
        }

        corpus = []
        #Iterating through all the tables
        for table in tables:
            cursor = database.execute("SELECT %s FROM %s" % (", ".join(tables[table]), table))
            # print cursor 
            rows = cursor.fetchall()
            #Iterating through the enries of the tables
            for row in rows:
                sentence = []
                for i, value in enumerate(row):
                    label = "%s.%s" % (table, tables[table][i])
                    # print label + " ---  label ---"
                    if " " in str(value):
                        #Assigning tokens to the column values 
                        tokens = word_tokenize(value)
                        for token in tokens:
                            sentence.append((token, label))
                            # print sentence 
                            # print " --- sentence --- "
                    else:
                        sentence.append((value, label))
                        # print sentence
                #Adding value of the complete table row into corpus datastructure
                corpus.append(sentence)
        # print corpus
        #Writing complete corpus list to a file
        pickle.dump(corpus, open(path, "wb"))
