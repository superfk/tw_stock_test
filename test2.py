#!/usr/bin/python
# -*- coding: utf8 -*-
'''
抓證交所的股票即時資料
tse  上市
otc  上櫃
http://mis.tse.com.tw/stock/fibest.jsp?stock=4506  可確認tse or otc
reference https://github.com/Asoul/tsrtc for detail
suck http://mis.twse.com.tw/stock/api/getStockInfo.jsp?json=1&delay=0&ex_ch=%20tse_1101.tw|tse_0050.tw
'''
import time
import json, csv
import requests
import sys
import time, random



def show_realtime(*stock_id):
    twse_url = 'http://mis.twse.com.tw/stock/api/getStockInfo.jsp'
    timestamp = int(time.time() * 1000 + 1000)
    channels = '|'.join('tse_{}.tw'.format(target_otc) for target_otc in stock_id)
    query_url = '{}?&ex_ch={}&json=1&delay=0&_={}'.format(twse_url, channels, timestamp)
#    headers = {'Accept-Language': 'zh-TW','User-Agent': 'My User Agent 1.0',}
    headers = {'Accept-Language': 'zh-TW','User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36',}
    req = requests.session()
    req.get('http://mis.twse.com.tw/stock/index.jsp', headers=headers)
    response = req.get(query_url)
#    print response.text
    if response.text.strip() == '':
        return 'nothing'

    content = json.loads(response.text, encoding='utf-8')
    data = content['msgArray']
#    return '\n'.join(x['n']+" : "+x['z']+","+x['t'] for x in data)
#    return data
    return '\n'.join([u'{n:10} {z:10} {t:10}'.format(**x) for x in data])



if __name__ == '__main__':
    with open('stockList_us.csv', newline='') as csvfile:
        # 讀取 CSV 檔案內容
        rows = csv.reader(csvfile)
        # 以迴圈輸出每一列
        l = []
        for row in rows:
            l.append(row[0])
        print(','.join(l))
    