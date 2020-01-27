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

#   http://www.twse.com.tw/exchangeReport/STOCK_DAY?date=20180817&stockNo=2330  取一個月的股價與成交量
def get_stock_history(date, stock_no):
    quotes = []
    url = 'http://www.twse.com.tw/exchangeReport/STOCK_DAY?date=%s&stockNo=%s' % ( date, stock_no)
    r = pxy.getRequest(url)
    # r = requests.get(url)
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
        stock.append(stock_no)
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

listDji = ['2354','2357','2454',1590,8454,6269,3034,6452,6456,6414,2723,3673,2049,3682,2498,2448,3189,5264,8150,2379,4958,9938,8464,6409,2353,2888,2101,2327,2376,2313,9914,2615,1722,2867,2106,1589,2451,2377,2392,1802,2542,2812,2809,2707,2347,9917,2206,9921,2352,1789,2103,3231,1434,2609,2610,6005,3037,2385,2603,2845,2849,2823,1262,1536,5871,9933,9945,2915,1717,2356,2204,1605,2618,2231,2059,9907,6176,1440,9910,2201,3702,1707,2015,2344,1477,2606,1227,2501,2834,1504,6239,2362,2449,1723,1319,5522,6285,2903,6415,2355,3044,2360]
[]
startDate = datetime.date(2010, 1, 1)
endDate = datetime.date(2019, 11, 1)
mArray = genMonthArr(startDate, endDate)
print(mArray)

reqCounts = 0
sqldb = DB()

for i in range(len(listDji)):
    sqldb.connect('tw_{}.db'.format(listDji[i]))
    for m in mArray:
        try:
            result = create_df(m, listDji[i])
            print(result)

            result.to_sql(name='stock_price', con=sqldb.conn, if_exists='append')
            #df = pd.read_sql_query('SELECT * FROM stock_price LIMIT 31 ORDER BY Index DESC',sqldb.conn)
            if reqCounts < 3:
                reqCounts += 1
                time.sleep(5+random.random()*5)
            else:
                reqCounts = 0
                time.sleep(5+random.random()*5)
            # print(result.groupby('month').close.count())  #每個月幾個營業日
            # print(result.groupby('month').shares.sum())  #每個月累計成交股數

        except Exception as e:
            print('')
            print('{} Error'.format(m))
            print(e)
    try:
        sqldb.close()
        export2excel('tw_{}'.format(listDji[i]), 'tw_{}'.format(listDji[i]))
        print('export ok!')
        print('')
    except Exception as e:
        print(e)




