from typing import Counter
import scrapy
import json
from bs4 import BeautifulSoup
import requests, traceback
import urllib.request
import random
from lxml.html import fromstring


class ProxyExampleSpider(scrapy.Spider):
    name = "proxy_example"
    allowed_domains = ["www.us-proxy.org"]
    start_urls = ['http://www.us-proxy.org']

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        trs = soup.select("#proxylisttable tr")
        for tr in trs:
            tds = tr.select("td")
            if len(tds) > 6:
                ip = tds[0].text
                port = tds[1].text
                anonymity = tds[4].text
                ifScheme = tds[6].text
                if ifScheme == 'yes':
                    scheme = 'https'
                else:
                    scheme = 'http'
                proxy = "%s://%s:%s" % (scheme, ip, port)
                meta = {
                    'port': port,
                    'proxy': proxy,
                    'dont_retry': True,
                    'download_timeout': 3,
                    '_proxy_scheme': scheme,
                    '_proxy_ip': ip
                }
                print(meta)
                yield scrapy.Request('https://httpbin.org/ip', callback=self.proxy_check_available, meta=meta, dont_filter=True)

    def proxy_check_available(self, response):
        proxy_ip = response.meta['_proxy_ip']
        if proxy_ip == json.loads(response.text)['origin']:
            yield {
                'scheme': response.meta['_proxy_scheme'],
                'proxy': response.meta['proxy'],
                'port': response.meta['port']
            }


class ProxyExample():
    name = "proxy_example"
    allowed_domains = ["www.us-proxy.org"]
    start_urls = ['http://www.us-proxy.org']

    def __init__(self):
        self.proxies = []
        self.meta = []

    def prepareValidProxies(self):
        response = requests.get('http://www.us-proxy.org')
        soup = BeautifulSoup(response.text, 'lxml')
        trs = soup.select("#proxylisttable tr")
        for tr in trs:
            tds = tr.select("td")
            if len(tds) > 6:
                ip = tds[0].text
                port = tds[1].text
                anonymity = tds[4].text
                ifScheme = tds[6].text
                if ifScheme == 'yes':
                    scheme = 'https'
                else:
                    scheme = 'http'
                proxy = "%s://%s:%s" % (scheme, ip, port)
                meta = {
                    'port': port,
                    'proxy': proxy,
                    'dont_retry': True,
                    'download_timeout': 5,
                    '_proxy_scheme': scheme,
                    '_proxy_ip': ip
                }
                self.meta.append(meta)

    def prepareValidProxies2(self):
        response = requests.get('https://free-proxy-list.net/')
        parser = fromstring(response.text)
        for i in parser.xpath('//tbody/tr')[:20]:
            if i.xpath('.//td[7][contains(text(),"no")]'):
                tds = i.xpath('.//td/text()')
                print(tds)
                # Grabbing IP and corresponding PORT
                if len(tds) > 6:
                    ip = tds[0]
                    port = tds[1]
                    anonymity = tds[4]
                    ifScheme = tds[6]
                    if ifScheme == 'yes':
                        scheme = 'https'
                    else:
                        scheme = 'http'
                    proxy = "%s://%s:%s" % (scheme, ip, port)
                    meta = {
                        'port': port,
                        'proxy': proxy,
                        'dont_retry': True,
                        'download_timeout': 5,
                        '_proxy_scheme': scheme,
                        '_proxy_ip': ip
                    }
                    self.meta.append(meta)

    def verify_proxy(self):
        for meta in self.meta:
            proxyOK = self.proxy_check_available(meta)
            if proxyOK:
                self.proxies.append({
                    'scheme': meta['_proxy_scheme'],
                    'proxy': meta['proxy'],
                    'port': meta['port']
                })
            if len(self.proxies) > 10:
                return

    def random_get_proxy(self):
        counts = 0
        while counts < 100:
            prxy = random.choice(self.proxies)
            proxy = f"{prxy['proxy']}"
            return proxy, prxy['scheme']

    def proxy_check_available(self, meta):
        pxy = meta['proxy']
        scheme = meta['_proxy_scheme']
        print(f'checking proxy: {pxy} with scheme {scheme}')
        try:
            response = requests.get(f'{scheme}://httpbin.org/ip', proxies={
                scheme: f'{pxy}'
            })
            checkIP = json.loads(response.text)['origin']
            if meta['_proxy_ip'] == checkIP:
                print(f"All was fine: check ip {checkIP}")
                return True
        except IOError:
            print(f"Connection error! (Check proxy)")
            return False

    def is_bad_proxy(self, proxy, scheme):
        try:
            resp = requests.get(
                "https://www.google.com.tw/",
                proxies={scheme: proxy}
            )
            if resp.status_code == 200:
                print("All was fine")
                return True
        except IOError:
            print("Connection error! (Check proxy)")
            return False
