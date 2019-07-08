from ConfigParser import ConfigParser


config = ConfigParser()


config['PATH'] = {
	
	'base': 'data',
	'stanford_jar': 'data/stanford-corenlp-full-2016-10-31/stanford-corenlp-3.7.0.jar',
	'stanford_models_jar': 'data/stanford-corenlp-full-2016-10-31/stanford-corenlp-3.7.0-models.jar',
	'stanford_models': 'data/stanford-corenlp-full-2016-10-31/stanford-corenlp-3.7.0-models/edu/stanford/nlp/models'

}


config['DATABASE']= {
	
	'hostname' : 'localhost',
	'username' : 'root',
	'password' : 'abdul',
	'database' : 'mydb',
	'graph_path' : 'data/graph.p',
	'corpus_path' : 'data/database_corpus.p'
}

config.write()