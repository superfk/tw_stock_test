#!/usr/bin/python
# -*- coding: utf8 -*-


# https://www.twse.com.tw/exchangeReport/STOCK_DAY?date=20100817&stockNo=2330

import numpy as np
import requests
import pandas as pd
import datetime
from dateutil import relativedelta
import calendar
import time
import random
from sqlalchemy import create_engine
from db_operation import DB
import proxy as pxy
from stock_export import export2excel
import config as cfg
import os, traceback

#   http://www.twse.com.tw/exchangeReport/STOCK_DAY?date=20180817&stockNo=2330  取一個月的股價與成交量
def get_stock_history(date, stock_no):
    quotes = []
    url = 'http://www.twse.com.tw/exchangeReport/STOCK_DAY?date=%s&stockNo=%s' % ( date, stock_no)
    # r = pxy.getRequest(url)
    r = requests.get(url)
    data = r.json()
    return transform(data['data'])  #進行資料格式轉換

def transform_date(date):
        y, m, d = date.split('/')
        return str(int(y)+1911) + '/' + m  + '/' + d  #民國轉西元
    
def transform_data(data):
    data[0] = datetime.datetime.strptime(transform_date(data[0]), '%Y/%m/%d')
    data[1] = int(data[1].replace(',', ''))  #把千進位的逗點去除
    data[2] = int(data[2].replace(',', ''))
    data[3] = float(data[3].replace(',', ''))
    data[4] = float(data[4].replace(',', ''))
    data[5] = float(data[5].replace(',', ''))
    data[6] = float(data[6].replace(',', ''))
    data[7] = float(0.0 if data[7].replace(',', '') == 'X0.00' else data[7].replace(',', ''))  # +/-/X表示漲/跌/不比價
    data[8] = int(data[8].replace(',', ''))
    return data

def transform(data):
    return [transform_data(d) for d in data]

def create_df(date,stock_no):
    s = pd.DataFrame(get_stock_history(date, stock_no))
    s.columns = ['date', 'shares', 'amount', 'open', 'high', 'low', 'close', 'change', 'turnover']
                #"日期","成交股數","成交金額","開盤價","最高價","最低價","收盤價","漲跌價差","成交筆數" 
    stock = []
    for i in range(len(s)):
        stock.append(str(stock_no))
    s['stockno'] = pd.Series(stock ,index=s.index)  #新增股票代碼欄，之後所有股票進入資料表才能知道是哪一張股票
    datelist = []
    for i in range(len(s)):
        datelist.append(s['date'][i])
    s.index = datelist  #索引值改成日期
    s2 = s.drop(['date'],axis = 1)  #刪除日期欄位
    mlist = []
    for item in s2.index:
        mlist.append(item.month)
    s2['month'] = mlist  #新增月份欄位
    return s2

def lastMonth(sourcedate):
    cur_m = sourcedate.month
    last_m = cur_m - 1
    last_y = sourcedate.year
    if last_m == 0:
        last_m = 12
        last_y -= 1
    return datetime.date(last_y, last_m, 1)


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)

def genMonthArr(startDate, endDate):
    m = []
    r = relativedelta.relativedelta(endDate, startDate)
    totalM = r.years*12 + r.months +1
    stY = startDate.year

    for i in range(totalM):
        nextDate = add_months(startDate, i)
        m.append(nextDate.strftime('%Y%m%d'))

    return m

def removeDuplicate(df_new, df_in_db):
    df_new.reset_index(inplace = True)
    print('reset df_new')
    print(df_new)
    df_in_db.reset_index()
    print('reset df_in_db')
    print(df_in_db)
    df_in_db = df_in_db.append(df_new, sort=False, ignore_index=True)
    print('append dataframe')
    print(df_in_db)
    print('')
    df_in_db.drop_duplicates(subset =["shares","amount","turnover"], 
                     keep = False, inplace = True) 
    df_in_db.set_index('index', inplace=True)
    return df_in_db

stockNOs = cfg.get_stocks()

# startDate = lastMonth(datetime.datetime.now())
# startDate = datetime.date(2020, 6, 1)
queryDates = cfg.get_dates()
startDate = queryDates['start']
endDate = queryDates['end']
monthArr = genMonthArr(startDate, endDate)
print(monthArr)

reqCounts = 0
sqldb = DB()
delaytime = cfg.get_delay()
dbfolder = cfg.get_db_folder()

for i in range(len(stockNOs)):
    dbpath = os.path.join(dbfolder,'tw_{}.db'.format(stockNOs[i]))

    sqldb.connect(dbpath)
    cursor = sqldb.conn.cursor() 
    sql_str = '''
            CREATE TABLE IF NOT EXISTS stock_price (
                "index" TIMESTAMP PRIMARY KEY,
                shares INTEGER,
                amount INTEGER,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                change REAL,
                turnover INTEGER,
                stockno TEXT,
                month integer
            );
            '''
    cursor.execute(sql_str)
    sqldb.conn.commit()
    for m in monthArr:
        try:
            result = create_df(m, f"{stockNOs[i]}")
            print('new acquired data')
            print(result)
            print('')
            sql_str = '''
            Select * FROM stock_price WHERE `index` >= '{}'
            '''.format(result.index[0])
            df_in_db = pd.read_sql(sql_str,sqldb.conn)
            print('existed data in database')
            print(df_in_db)
            print('')
            remain_df = removeDuplicate(result, df_in_db)
            print('after removing')
            print(remain_df)

            remain_df.to_sql(name='stock_price', con=sqldb.conn, if_exists='append')
            #df = pd.read_sql_query('SELECT * FROM stock_price LIMIT 31 ORDER BY Index DESC',sqldb.conn)
            if reqCounts < 3:
                reqCounts += 1
                time.sleep(delaytime+random.random()*5)
            else:
                reqCounts = 0
                time.sleep(delaytime+random.random()*5)
            # print(result.groupby('month').close.count())  #每個月幾個營業日
            # print(result.groupby('month').shares.sum())  #每個月累計成交股數

        except Exception as e:
            errorMsg = traceback.format_exc()
            print('')
            print('{} Error'.format(m))
            print(f'{errorMsg}')
            time.sleep(delaytime+random.random()*5)
    try:
        sqldb.close()
        export2excel(dbpath, 'excel/tw_{}'.format(stockNOs[i]))
        print('export ok!')
        print('')
    except Exception as e:
        print(e)



