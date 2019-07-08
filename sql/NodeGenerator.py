from sql.nodes.AttributeNode import AttributeNode
from sql.nodes.FunctionNode import FunctionNode
# from sql.nodes.FunctionNode import FunctionNode2
from sql.nodes.FunctionNodeType import FunctionNodeType
from sql.nodes.SelectNode import SelectNode
from sql.nodes.TableNode import TableNode
from sql.nodes.ValueNode import ValueNode
from sql.nodes.LimitNode import LimitNode
from sql.nodes.IntermediateNode import IntermediateNode
from sql.NodeSelector import NodeSelector
from sql.NodeReducer import NodeReducer


class NodeGenerator(object):
    def __init__(self, communicator):
        self.communicator = communicator

        self.tagged = {}
        self.parse = None

        selector = NodeSelector(communicator)
        reducer = NodeReducer()

        self.pipeline = [selector, reducer]


    def __call__(self, doc):
        self.tagged = doc['tagged']
        self.parse = doc['dep_parse']
        # print "generate_tree start : \n\n"
        tree = self.generate_tree(self.parse.root)
        # print tree
        # (SelectNode['*'] TableNode['customer'])

        for process in self.pipeline:
            tree = process(tree)
        # print "generate_tree end here : \n\n"
        return tree
        

    def generate_tree(self, node):
        tree = self.get_node_type(node)
        # print 'tree [ ' , tree, ' ] \n'
        # tree [  (SelectNode['*'])  ] 
        # tree [  (TableNode['customer'])  ] 
        # tree [  None  ]


        for _, key in node['deps'].items():
            # print 'key : '+str(int(key[0]))
            idx = int(key[0])

            result = self.generate_tree(self.parse.nodes[idx])
            if not result:
                continue

            if tree:
                tree.add_child(result)
                result.add_parent(tree)
            else:
                tree = result
            # print tree , '\n'
        return tree


    def get_node_type(self, node):
        token = node['word']

        # print 'token [ ', token ,' ]'
        # print 'NNode [ ', node ,' ]\n'

        # First check is to see if the token has been tagged
        # By any of our classifiers. If it hasn't we can ignore
        # The token

        if not token in self.tagged:
            return None

        node_type = self.tagged[token]['type']
        node_tag = self.tagged[token]['tags']

        # Ignore tokens tagged as IGN
        if node_tag == "IGN":
            return None

        # Dynamically create method to call
        method_name = "get_%s_node" % node_type
        try:
            method = getattr(self, method_name)

        except AttributeError:
            self.communicator.error("No method for node type: %s" % node_type)
        
        return method(node, node_tag)


    def get_grammar_node(self, node, tag):
        # print '---- grammar ---'
        # u'word': u'show'
        token = node['word']
        # token = show
        # tag = SELECT

        # print '[ Token : ' , token ,'\n Node' , node, '\n Tag', tag ,' ]\n'
        
        if tag == "SELECT":
            return SelectNode()

        if tag == "COUNT":
            return FunctionNode(func_type=FunctionNodeType.COUNT)

        if tag == "SUM":
            return FunctionNode(func_type=FunctionNodeType.SUM)

        if tag == "AVG":
            return FunctionNode(func_type=FunctionNodeType.AVG)

        if tag == "MAX":
            return FunctionNode(func_type=FunctionNodeType.MAX)

        if tag == "MIN":
            return FunctionNode(func_type=FunctionNodeType.MIN)

        if tag == "LIMIT":
            return LimitNode(token)

        if tag == "Like":
            return LimitNode(token)
        print tag
        self.communicator.error("Not handling grammar tag: %s" % tag)


    @staticmethod
    def get_schema_node(node, tags):

        # print '--- Schema --- '
        token = node['word']
        # print '[ Token : ' , token ,'\nNode' , node, '\nTags ', tags ,' ]\n'
        
        # Because the Node Type for this object is either Schema or Corpus
        # We can safely make the assumption that the Node Tag will be a list
        
        tag, score = tags[0]
        # print tag , ' mytaggg'
        # print score , ' Score'
        if score < 1.0:
            return IntermediateNode('schema', token, tags)

        if "." in tag:
            return AttributeNode(tag)
        else:
            return TableNode(tag)


    @staticmethod
    def get_corpus_node(node, tags):
        # print '--- corpus --- '

        token = node['word']
        # print '[ Token : ' , token ,'\n Node' , node, '\n Tag', tags ,' ]\n'


        # Because the Node Type for this object is either Schema or Corpus
        # We can safely make the assumption that the Node Tag will be a list
        tag, score = tags[0]

        if score < 1.0:
            return IntermediateNode('corpus', token, tags)

        return ValueNode(token, tag)
