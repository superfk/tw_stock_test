#!/usr/bin/python
# -*- coding: utf8 -*-


# https://www.twse.com.tw/exchangeReport/STOCK_DAY?date=20100817&stockNo=2330

import webbrowser
import time

def downloadHistory(stock_no):
    url = r"https://query1.finance.yahoo.com/v7/finance/download/{}.TW?period1=946656000&period2=1572710400&interval=1d&events=history&crumb=t/XHPSAFTad".format(stock_no)
    webbrowser.open(url, new = 0)

webbrowser.open('google.com', new = 0)

listDji = [2317]


for i in range(len(listDji)):
    try:
        downloadHistory(listDji[i])
        time.sleep(5)
    except Exception as e:
        print(e)
       




