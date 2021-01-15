from typing import Counter
import scrapy
import json
from bs4 import BeautifulSoup
import requests
import urllib.request
import random


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
                print(meta)
                proxyOK = self.is_bad_proxy(proxy, scheme)
                if proxyOK:
                    self.proxies.append({
                        'scheme': meta['_proxy_scheme'],
                        'proxy': meta['proxy'],
                        'port': meta['port']
                    })
                if len(self.proxies) > 10:
                    return
                # response = requests.get('https://httpbin.org/ip')
                # checkIP = json.loads(response.text)['origin']
                # print(checkIP)
                # if meta['_proxy_ip'] == checkIP:
                #     self.proxies.append({
                #         'scheme': meta['_proxy_scheme'],
                #         'proxy': meta['proxy'],
                #         'port': meta['port']
                #     })

    def random_get_proxy(self):
        counts = 0
        print(self.proxies)
        while counts < 100:
            prxy = random.choice(self.proxies)
            proxy = f"{prxy['proxy']}"
            return proxy, prxy['scheme']

    def proxy_check_available(self, response):
        proxy_ip = response.meta['_proxy_ip']
        if proxy_ip == json.loads(response.text)['origin']:
            return {
                'scheme': response.meta['_proxy_scheme'],
                'proxy': response.meta['proxy'],
                'port': response.meta['port']
            }

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
