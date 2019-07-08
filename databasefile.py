from Config import Config
import pymysql
import cPickle as pickle
from _mysql_exceptions import OperationalError

"""
Communicates with a MySQL database
"""
class Database(object):

    def __init__(self, use_db_name=True):
    #     config = Config()
    #     db_settings = dict(config.items("DATABASE"))
    #     # print db_settings
    # #{'username': 'root', 'corpus_path': 'data/database_corpus.p', 
    # #'database': 'mydb', 'hostname': 'localhost', 'graph_path': 'data/graph.p', 'password': 'abdul'}

    #     config = {
    #         'host': db_settings["hostname"],
    #         'user': db_settings["username"],
    #         'passwd': db_settings["password"]
    #     }
        if use_db_name:
            db = 'mydb'

        try:
            self.database = pymysql.connect( host='localhost', user='root', passwd='abdul', db='mydb' )
        except OperationalError as (_, error):
            raise ValueError('Incorrect settings given for the database. %s' % error)

    def set_db(self, db_name):
        try:
            self.database.select_db(db_name)
            self.database.commit()
        except OperationalError as (_, error):
            raise ValueError('Incorrect name given for the database. %s' % error)

    def get_tables(self):
        cursor = self.execute("SHOW TABLES;")
        return cursor.fetchall()


    def get_fields(self, table):
        cursor = self.execute("DESCRIBE %s" % table)
        return cursor.fetchall()

    def get_foreign_keys(self):
        cursor = self.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()[0]

        self.set_db("INFORMATION_SCHEMA")

        cursor = self.execute("""SELECT TABLE_NAME,COLUMN_NAME,CONSTRAINT_NAME,
            REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME from KEY_COLUMN_USAGE WHERE
            TABLE_SCHEMA = "%s" and referenced_column_name is not NULL;""" % current_db)

        foreign_keys = cursor.fetchall()
        
        self.set_db(current_db)

        return foreign_keys

    def execute(self, statement, show=False):
        cursor = self.database.cursor()
        cursor.execute(statement)

        if show:
            columns = []
            tavnit = '|'
            separator = '+'

            results = cursor.fetchall()

            if not results:
                print "\n   %s\n" % "No results found."
                return

            sizetable = [map(len, map(str, row)) for row in results]
            # print sizetable
            widths = map(max, zip(*sizetable))
            # print widths
            # reading column of tables
            for cd in cursor.description:
                columns.append(cd[0])
            # print columns
            columns_widths = []
            # get the size of columns
            for cols_ls in columns:
                columns_widths.append(len(cols_ls))
            # print columns_widths

            new_widths = []
            for i in range(0, len(widths)):
                new_widths.append(widths[i] + columns_widths[i])

            # print new_widths

            for w in new_widths:
                tavnit += " %-" + "%ss |" % (w,)
                separator += '-' * w + '--+'

            print separator
            print tavnit % tuple(columns)
            print separator
            
            for row in results:
                print tavnit % row
            print separator

        return cursor

"""
Handles the nodes data for Table Names and Attributes
"""
class NodeType(object):
    TABLE = 1
    ATTRIBUTE = 2

"""
Handles the nodes data for Table Names and Attributes
"""

class Node(object):
    def __init__(self, table, attribute=None):
        self.table = table

        if attribute is None:
            self.type = NodeType.TABLE
            self.label = self.table
            self.attributes = []
            self.relations = []
        else:
            self.attribute = attribute
            self.type = NodeType.ATTRIBUTE
            self.label = "%s.%s" % (self.table, self.attribute)

    def add_attribute(self, node):
        if self.type is not NodeType.TABLE:
            raise TypeError("Attribute Node does not contain attributes")

        self.attributes.append(node.label)


    def add_relation(self, node, self_key, foreign_key):
        if self.type is not NodeType.TABLE:
            raise TypeError("Attribute Node does not contain relations")

        self.relations.append((node.label, self_key, foreign_key))

    def __repr__(self):
        return "%s['%s']" % (type(self).__name__, self.table)


"""
Creates a Schema Graph containing mapping of All Tables, Attributes, Primary Keys and Foreign Keys
"""
class SchemaGraph(object):

    def __init__(self, file_path=None):
        if file_path is None:
            self.graph_dict = {}
        else:
            self.graph_dict = pickle.load(open(file_path, "rb"))

    def get_node(self, label):
        return self.graph_dict[label]

    def add_node(self, node):
        if node.label not in self.graph_dict:
            self.graph_dict[node.label] = node
    
    def nodes(self, type=None):
        if type is None:
            return self.graph_dict.keys()
            # ['customer', 'customer.zipcode', 'orderinfo', 'revenue', 'customer.addressline', 'customer.customer_id', 'revenue.id', 'orderinfo.cust_id', 'customer.name', 'orderinfo.date_placed', 'customer.title', 'customer.town', 'orderinfo.orderinfo_id', 'orderinfo.salary', 'customer.phone', 'revenue.name', 'orderinfo.date_shipped']

        return [node.label for node in self.graph_dict.values() if node.type == type]

    def get_direct_path(self, table_name_a, table_name_b):
        queue = [(table_name_a, [])]
        while queue:
            # print queue
            (vertex, path) = queue.pop(0)
            # print vertex , path 
            node = self.get_node(vertex)
          #  print node
            for next in node.relations:
                # print next[0]
                if next[0] == table_name_b:
                    return path + [next]
                else:
                    queue.append((next[0], path + [next]))
                    
    #Constructs a list of all the database node mappings and stores in graph.p file
    def construct(self, database, file_path):
        for (table_name,) in database.get_tables():
            #print table_name
            table = Node(table_name)
            self.add_node(table)

            fields = database.get_fields(table_name)
           # print fields
            for field in fields:
                attribute = Node(table_name, field[0])
                table.add_attribute(attribute)
                self.add_node(attribute)

        for table, self_key, _, foreign_table, foreign_key in database.get_foreign_keys():
            # print str(table)+" <---  table " + str(self_key)+" <-- PK " + str(foreign_table)+" <-- FKtable " + str(foreign_key)
            table_node = self.get_node(table)
            # print "Table Node:::"+str(table_node)
            foreign_node = self.get_node(foreign_table)
            # print "Foreign Node:::"+str(foreign_node) 
            #Add the data of the current table attributes
            table_node.add_relation(foreign_node, self_key, foreign_key)
            #Add the data of the foreign attributes of the table
            foreign_node.add_relation(table_node, foreign_key, self_key)
            # print('\n\n')
        ##print self.graph_dict
        
        #Store the complete graph_dict list to a file
        pickle.dump(self.graph_dict, open(file_path, "wb"))
