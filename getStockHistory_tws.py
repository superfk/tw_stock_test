#!/usr/bin/python
# -*- coding: utf8 -*-


# https://www.twse.com.tw/exchangeReport/STOCK_DAY?date=20100817&stockNo=2330

import numpy as np
import requests
import pandas as pd
import datetime, time
from dateutil import relativedelta
import calendar
import time
import random
from sqlalchemy import create_engine
from db_operation import DB
import proxy as pxy
from stock_export import export2excel
import config as cfg
import os
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from pandas_datareader import data as web


dbFolder = os.path.join(cfg.get_db_folder(), 'yahoo',  cfg.get_country())
if not os.path.exists(dbFolder):
    os.makedirs(dbFolder)

class TWStock():
    def __init__(self):
        self.df = None
        self.cursor = None
        self.stockNOs = cfg.get_stocks()
        self.startDate = cfg.get_dates()['start']
        self.endDate = cfg.get_dates()['end']
        self.monthArr = self.genMonthArr(self.startDate, self.endDate)
        self.sqldb = DB()
        self.delaytime = cfg.get_delay()
        self.dbfolder = cfg.get_db_folder()
        self.rndDelay = 0.1
        self.columns = ['date', 'shares', 'amount', 'open',
                        'high', 'low', 'close', 'change', 'turnover']
        self.reqCounts = 0
        self.country = cfg.get_country()
        self.financeType = 'twse'

    def prepareFolder(self, stockNo):
        # dbFolder = os.path.join(self.dbfolder, self.financeType,  self.country)
        # if not os.path.exists(dbFolder):
        #     os.makedirs(dbFolder)
        return os.path.join(dbFolder, f'{self.country}_{stockNo}.db')

    def openDb(self, stockNo):
        dbpath = self.prepareFolder(stockNo)
        self.sqldb.connect(dbpath)
        self.cursor = self.sqldb.conn.cursor()
        sql_str = '''
                CREATE TABLE IF NOT EXISTS stock_price (
                    "date" TIMESTAMP PRIMARY KEY,
                    shares INTEGER,
                    amount INTEGER,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    change REAL,
                    turnover INTEGER,
                    stockno TEXT,
                    month INTEGER
                );
                '''
        self.cursor.execute(sql_str)
        self.sqldb.conn.commit()

    def get_stock_history(self, stockNo, startDate, endDate=None, use_proxy=False):
        url = f'http://www.twse.com.tw/exchangeReport/STOCK_DAY?date={startDate}&stockNo={stockNo}'
        if use_proxy:
            r = pxy.getRequest(url)
        else:
            r = requests.get(url)
        data = r.json()
        return self.transform(data['data'])  # 進行資料格式轉換

    def arrange(self, result, stock_no):
        s = pd.DataFrame(result)
        s.columns = self.columns
        # "日期","成交股數","成交金額","開盤價","最高價","最低價","收盤價","漲跌價差","成交筆數"
        stock = [str(stock_no) for i in range(len(s))]
        # 新增股票代碼欄，之後所有股票進入資料表才能知道是哪一張股票
        s['stockno'] = pd.Series(stock, index=s.index)
        datelist = [s['date'][i] for i in range(len(s))]
        s.index = datelist  # 索引值改成日期
        s2 = s.drop(['date'], axis=1)  # 刪除日期欄位
        mlist = [x.month for x in s2.index]
        s2['month'] = mlist  # 新增月份欄位
        return s2

    def run(self, stockNo, use_proxy=False):
        for m in self.monthArr:
            try:
                result = self.get_stock_history(
                    stockNo=stockNo, startDate=m, endDate=None, use_proxy=use_proxy)
                result = self.arrange(result, stockNo)
                print('new acquired data')
                print(result)
                print('')
                sql_str = '''
                Select * FROM stock_price WHERE `index` >= '{}'
                '''.format(result.index[0])
                df_in_db = pd.read_sql(sql_str, self.sqldb.conn)
                print('existed data in database')
                print(df_in_db)
                print('')
                remain_df = self.removeDuplicate(result, df_in_db)
                print('after removing')
                print(remain_df)
                remain_df.to_sql(
                    name='stock_price', con=self.sqldb.conn, if_exists='append', chunksize=250)
            except:
                errorMsg = traceback.format_exc()
                print('')
                print('{} Error'.format(m))
                print(f'{errorMsg}')
            finally:
                if self.reqCounts < 3:
                    self.reqCounts += 1
                    time.sleep(self.delaytime+random.random()*self.rndDelay)
                else:
                    self.reqCounts = 0
                    time.sleep(self.delaytime+random.random()*self.rndDelay)

    def closeDb(self):
        self.sqldb.close()

    def transform_date(self, date):
        y, m, d = date.split('/')
        return str(int(y)+1911) + '/' + m + '/' + d  # 民國轉西元

    def transform_data(self, data):
        data[0] = datetime.datetime.strptime(
            self.transform_date(data[0]), '%Y/%m/%d')
        data[1] = int(data[1].replace(',', ''))  # 把千進位的逗點去除
        data[2] = int(data[2].replace(',', ''))
        data[3] = float(data[3].replace(',', ''))
        data[4] = float(data[4].replace(',', ''))
        data[5] = float(data[5].replace(',', ''))
        data[6] = float(data[6].replace(',', ''))
        data[7] = float(0.0 if data[7].replace(',', '') ==
                        'X0.00' else data[7].replace(',', ''))  # +/-/X表示漲/跌/不比價
        data[8] = int(data[8].replace(',', ''))
        return data

    def transform(self, data):
        return [self.transform_data(d) for d in data]

    def lastMonth(self, sourcedate):
        cur_m = sourcedate.month
        last_m = cur_m - 1
        last_y = sourcedate.year
        if last_m == 0:
            last_m = 12
            last_y -= 1
        return datetime.date(last_y, last_m, 1)

    def add_months(self, sourcedate, months):
        month = sourcedate.month - 1 + months
        year = sourcedate.year + month // 12
        month = month % 12 + 1
        day = min(sourcedate.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)

    def genMonthArr(self, startDate, endDate):
        m = []
        r = relativedelta.relativedelta(endDate, startDate)
        totalM = r.years*12 + r.months + 1
        stY = startDate.year

        for i in range(totalM):
            nextDate = self.add_months(startDate, i)
            m.append(nextDate.strftime('%Y%m%d'))
        return m

    def genDaysInMonth(self, curmonth):
        days = calendar.monthrange(curmonth.year, curmonth.month)[1]
        d = []
        for i in range(days):
            fmtDate = datetime.date(
                curmonth.year, curmonth.month, i+1).strftime('%Y%m%d')
            d.append(fmtDate)
        return d

    def removeDuplicate(self, df_new, df_in_db):
        df_new.reset_index(inplace=True)
        print('reset df_new')
        print(df_new)
        df_in_db.reset_index()
        print('reset df_in_db')
        print(df_in_db)
        df_in_db = df_in_db.append(df_new, sort=False, ignore_index=True)
        print('append dataframe')
        print(df_in_db)
        print('')
        df_in_db.drop_duplicates(subset=["shares", "amount", "turnover"],
                                 keep=False, inplace=True)
        df_in_db.set_index('index', inplace=True)
        return df_in_db


class YahooStock(TWStock):
    def __init__(self):
        super(YahooStock, self).__init__()
        self.columns = ['date', 'high', 'low', 'open',
                        'close', 'volume', 'adj_close']
        self.financeType = 'yahoo'

    def openDb(self, stockNo):
        dbpath = self.prepareFolder(stockNo)
        self.sqldb.connect(dbpath)
        self.cursor = self.sqldb.conn.cursor()
        sql_str = '''
                CREATE TABLE IF NOT EXISTS stock_price (
                    "date" TIMESTAMP PRIMARY KEY,
                    volume INTEGER,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    adj_close REAL,
                    stockno TEXT,
                    month INTEGER
                );
                '''
        self.cursor.execute(sql_str)
        self.sqldb.conn.commit()

    def get_stock_history(self, stockNo, startDate, endDate=None, use_proxy=False):
        stockNoCode = stockNo
        if self.country == 'tw':
            stockNoCode = f"{stockNo}.tw"
            try:
                df = web.DataReader(f"{stockNoCode}", 'yahoo',
                                start=startDate, end=endDate)
                                
                df.reset_index(inplace=True)
                
                return df
            except:
                stockNoCode = f"{stockNo}.two"
                df = web.DataReader(f"{stockNoCode}", 'yahoo',
                                start=startDate, end=endDate)
                                
                df.reset_index(inplace=True)
                
                return df
        else:
            try:
                df = web.DataReader(f"{stockNoCode}", 'yahoo',
                                start=startDate, end=endDate)
                                
                df.reset_index(inplace=True)
                
                return df
            except:
                print('Not Found Stock No.')

    def arrange(self, df, stock_no):
        df.columns = self.columns
        stock = [str(stock_no) for i in range(len(df))]
        # 新增股票代碼欄，之後所有股票進入資料表才能知道是哪一張股票
        df['stockno'] = pd.Series(stock, index=df.index)
        # datelist = [df['date'][i] for i in range(len(df))]
        # df.index = datelist  # 索引值改成日期
        # s2 = df.drop(['date'], axis=1)  # 刪除日期欄位
        mlist = [x.month for x in df['date']]
        df['month'] = mlist  # 新增月份欄位
        return df

    def run(self, stockNo, use_proxy=False):
        startT = time.time()
        while True:
            try:
                print(f'running {stockNo} stock')
                result = self.get_stock_history(
                    stockNo=stockNo, startDate=self.startDate, endDate=self.endDate, use_proxy=use_proxy)
                result = self.arrange(result, stockNo)

                sql_str = '''
                Select * FROM stock_price WHERE `date` >= '{}'
                '''.format(result.index[0])

                df_in_db = pd.read_sql(sql_str, self.sqldb.conn)
                
                remain_df = self.removeDuplicate(result, df_in_db)
                
                # print(remain_df)
                remain_df.to_sql(
                    name='stock_price', con=self.sqldb.conn, if_exists='append', chunksize=250)
                
                endT = time.time()
                exeT = endT - startT
                print(f'finished {stockNo} stock, executed time is {exeT}')
                return True
            except:
                errorMsg = traceback.format_exc()
                print('')
                print(f'{errorMsg}')
            finally:
                if self.reqCounts < 3:
                    self.reqCounts += 1
                    time.sleep(self.delaytime+random.random()*self.rndDelay)
                else:
                    self.reqCounts = 0
                    time.sleep(self.delaytime+random.random()*self.rndDelay)
                    return False

    def removeDuplicate(self, df_new, df_in_db):
        df_new.reset_index(inplace=True)
        df_new['date'] = pd.to_datetime(df_new['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df_in_db.reset_index()
        df_in_db = df_in_db.append(df_new, sort=False, ignore_index=True)
        df_in_db.drop_duplicates(subset=["date"],
                                 keep=False, inplace=True)
        df_in_db.set_index('date', inplace=True)
        df_in_db = df_in_db.drop(['index'], axis=1)
        return df_in_db

def run_instance(stockNo):
    st = YahooStock()
    st.openDb(stockNo)
    result = st.run(stockNo)
    st.closeDb()
    return result, stockNo
        

def main():
    # st = TWStock()
    # tasks = [run_instance(s) for s in cfg.get_stocks()]
    # results = await asyncio.gather(*tasks, return_exceptions=True)
    startT = time.time()
    workers = 20
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for s in cfg.get_stocks():
            future = executor.submit(run_instance, s)
            print(type(future))
            futures.append(future)
        totalStocks = len(futures)
        success_tasks = 0
        invalidTasks = []
        for future in as_completed(futures):
            success, stkNo = future.result()
            if success:
                success_tasks += 1
            else:
                invalidTasks.append(stkNo)
    endT = time.time()
    exeT = endT - startT
    invalidStk = ",".join(invalidTasks)
    print(f"executed time: {exeT} s for {workers} workers, successTasks {success_tasks}/{totalStocks}, invalid stock: {invalidStk}")

if __name__ == '__main__':
    main()
