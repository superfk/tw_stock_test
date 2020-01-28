import requests
import bs4


url = 'http://pchome.megatime.com.tw/group/mkt5/cidE002.html'

htmlfile = requests.get(url)
print(htmlfile.text)
objSoup = bs4.BeautifulSoup(htmlfile.text, 'lxml')

if htmlfile.status_code == requests.codes.ok:
    print('Response ok')
    stocks = objSoup.select('table tbody tr')
    print(stocks)
    for s in stocks:
        print(s)
