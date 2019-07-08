from sql.nodes.SQLNode import SQLNode
from sql.nodes.SQLNodeType import SQLNodeType



class FunctionNode(SQLNode):
    
    def __init__(self, child=None, func_type=None, parent=None):
        if func_type == 'COUNT':
            super(FunctionNode, self).__init__( "COUNT(*)", "select")
        elif func_type == 'SUM':
            super(FunctionNode, self).__init__( "SUM(salary)", "select")
        elif func_type == 'AVG':
            super(FunctionNode, self).__init__( "AVG(*)", "select")
        elif func_type == 'MIN':
            super(FunctionNode, self).__init__( "MIN(*)", "select")
        elif func_type == 'MAX':
            super(FunctionNode, self).__init__( "MAX(*)", "select")


        self.add_child(child)
        self.add_parent(parent)

        self.func_type = func_type


    def __repr__(self):
        return "%s['%s']" % (type(self).__name__, self.func_type)

