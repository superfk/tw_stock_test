from db_operation import DB
import pandas as pd


def export2excel(db_name,filename):
    d = DB()
    # open a file to write to
    d.connect('{}.db'.format(db_name))
    # connect to your database
    df = pd.read_sql_query('SELECT * FROM stock_price',d.conn)
    df.to_excel("{}.xlsx".format(filename))