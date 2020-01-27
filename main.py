import requests
import bs4
import csv
import pandas as pd
import sys, os
import json
import datetime, calendar

def getHistory(stock_no, date):
    try:
        url = r'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={}&stockNo={}'.format(date, stock_no)
        htmlfile = requests.get(url)

        resp_text = json.loads(htmlfile.text, encoding='utf-8-sig')
        head = resp_text['fields']
        data = resp_text['data']
        dataset = []
        for d in data:
            singleDict = dict(zip(head, d))
            dataset.append(singleDict)
        df = pd.DataFrame(dataset)
        return df   
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, exc_type, fname, exc_tb.tb_lineno)

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)

def genDateSeries(fromDate, ToDate):
    fromD = datetime.datetime.strptime(fromDate,'%Y%m%d')
    toD = datetime.datetime.strptime(ToDate,'%Y%m%d')
    diffM = (toD.year - fromD.year) * 12 + toD.month - fromD.month +1
    print(diffM)
    dateArr = []
    for d in range(diffM):
        newDate = add_months(fromD,d)
        strDate = newDate.strftime('%Y%m%d')
        dateArr.append(strDate)
    return dateArr

def main():
    datefrom = '20100115'
    dateTo = '20200130'
    stock = '2317'
    dateArr = genDateSeries(datefrom, dateTo)
    print(dateArr)
    dfArr = []
    for d in dateArr:
        df = getHistory(stock, d)
        dfArr.append(df)
    df = pd.concat(dfArr)
    print(df)

if __name__ == '__main__':
    main()