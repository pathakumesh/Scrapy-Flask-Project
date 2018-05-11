# -*- coding: utf-8 -*-

import re
import json
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["healthline.com"]
    quotes_base_url = "https://frontend-prod.healthline.com/api/nutrition/feed?rows=10&start=%s"
    current_index = 10
    start_urls = [quotes_base_url % current_index]

    def parse(self, response):
        data = json.loads(response.body)
        print 'current_index ', self.current_index
        current_items = data.get('items',[])
        maximum_times = data.get('maxNumItems')
        for post in current_items:
            item = BlogExtractItem()
            
            item['title'] = post['title'][0]
            item['link'] = post['link']
            
            request = scrapy.Request(item['link'], self.parse_sub_blog)
            request.meta['item'] = item
            yield request

        self.current_index += 10
        if self.current_index < maximum_times:
            yield scrapy.Request(self.quotes_base_url % self.current_index)
        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0

        item['author'] = response.xpath('//div[@class= "css-1gby43k"]/a/text()').extract_first()
        item['date'] = response.xpath('//div[@class= "css-1gby43k"]').re(r'.*on\s*(.*?)<')[0]

        # Find the actual article block
        article = response.xpath('//article[@class= "article-body css-11mv9wc"]/*')
        for sub_block in article:            
            #Extract the plain text and count the words
            block_line = sub_block.xpath('string()').extract()[0]
            word_count += get_word_count(block_line)

        item['word_count'] = word_count
        yield item


def get_word_count(string):
    count = count_after_replacing_special_chars(string)
    return count

def count_after_replacing_special_chars(string):
    #Proceed such that unicode characters are properly handled
    
    updated_line = [line.decode('utf-8').strip() for line in string.encode('utf-8').split('\n')]
    l_count = 0
    for _line in updated_line:
        if len(_line) > 0:

            #end if  javascript notations are there.
            if 'function()' in _line:
                break
            #remove bullets and special characters
            _line = re.sub(u'\u25cf\t', '', _line)
            _line = re.sub(u'\u2013', '-', _line)
            _line = _line.replace('- ', ' ')
            l_count += len(_line.split())
    return l_count

def replace_special_chars(string):
    #Proceed such that unicode characters are properly handled
    string = string.encode('utf-8')
    string = string.replace("\xe2\x80\x93", "-")
    string = string.replace("\xe2\x80\x99", "'")
    string = string.replace("\xe2\x80\x9d", "\"").replace("\xe2\x80\x9c", "\"")
    string = string.replace("\xc2\xae", "®")
    
    return string
    



            