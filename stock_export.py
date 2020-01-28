from db_operation import DB
import pandas as pd


def export2excel(db_name,filename):
    d = DB()
    # open a file to write to
    d.connect('{}.db'.format(db_name))
    # connect to your database
    df = pd.read_sql_query('SELECT * FROM stock_price',d.conn)
    df.to_excel("{}.xlsx".format(filename))

def export2dataframe(db_name):
    d = DB()
    # open a file to write to
    d.connect('{}.db'.format(db_name))
    # connect to your database
    df = pd.read_sql_query('SELECT * FROM stock_price',d.conn)
    return df

def main():
    export2excel('tw_2330','tw_2330')



if __name__ =='__main__':
    main()