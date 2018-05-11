from scrapy.http import HtmlResponse
from bs4 import BeautifulSoup
import requests
import json

def get_proxy_into_local_file_as_list():
	with open('proxy_list.json', 'w+b') as proxy_file:
	    url = 'https://free-proxy-list.net/'
	    response = requests.get(url)
	    parser = HtmlResponse(url="my HTML string", body=response.content)
	    proxies = set()
	    for i in parser.xpath('//tbody/tr')[:20]:
	        if i.xpath('.//td[7][contains(text(),"yes")]'):
	            proxy = ":".join([i.xpath('.//td[1]/text()').extract()[0], i.xpath('.//td[2]/text()').extract()[0]])
	            proxies.add(proxy)
	    
	    proxy_list = list(proxies)
	    json.dump(proxy_list, proxy_file)
	    

def get_proxy_into_local_file():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text)
    tables = soup.findChildren('table', attrs={'class': 'table table-striped table-bordered dataTable'})
    rows = my_table.findChildren(['th', 'tr'])
    for row in rows:
    	cells = row.findChildren('td')
    	for cell in cells:
    		value = cell.string
    		print "The value in this cell is %s" % value
get_proxy_into_local_file()
# get_proxy_into_local_file_as_list()