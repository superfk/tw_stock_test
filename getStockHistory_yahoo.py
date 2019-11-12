#!/usr/bin/python
# -*- coding: utf8 -*-


# https://www.twse.com.tw/exchangeReport/STOCK_DAY?date=20100817&stockNo=2330

import webbrowser
import time

def downloadHistory(stock_no):
    url = r"https://finance.yahoo.com/quote/{}.TW/history?period1=726163200&period2=1572796800&interval=1d&filter=history&frequency=1d".format(stock_no)
    print(url)
    webbrowser.open(url, new = 0, autoraise=False)

listDji = [2317]

for i in range(len(listDji)):
    try:
        downloadHistory(listDji[i])
        time.sleep(5)
    except Exception as e:
        print(e)
       




