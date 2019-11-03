import sqlite3
from sqlite3 import Error
 

class DB(object):
    def __init__(self):
        self.conn = None

    def connect(self, db_file):
        """ create a database connection to a SQLite database """
        try:
            self.conn = sqlite3.connect(db_file)
            return True
        except:
            return None
    
    def close(self):
        self.conn.close()
