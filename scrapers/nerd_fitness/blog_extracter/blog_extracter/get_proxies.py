from scrapy.http import HtmlResponse
import requests

def get_proxy_into_local_file():
	with open('blog_extracter/proxy_list.txt', 'w+b') as proxy_file:
	    url = 'https://free-proxy-list.net/'
	    response = requests.get(url)
	    parser = HtmlResponse(url="my HTML string", body=response.content)
	    proxies = set()
	    for i in parser.xpath('//tbody/tr')[:20]:
	        if i.xpath('.//td[7][contains(text(),"yes")]'):
	            proxy = ":".join([i.xpath('.//td[1]/text()').extract()[0], i.xpath('.//td[2]/text()').extract()[0]])
	            proxies.add(proxy)
	    
	    for p in proxies:
	    	proxy_file.write('https://%s\n' % p)
get_proxy_into_local_file()