# -*- coding: utf-8 -*-

import re
import scrapy
import requests
import logging as log
from blog_extracter.items import BlogExtractItem

class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["zenhabits.net"]
    start_urls = ['https://zenhabits.net/archives/']

    
    def parse(self, response):
        blog_posts = response.xpath('//td[@id]')
        for sub_blog in  blog_posts:
            item = BlogExtractItem()
            #Get Title, Link, Date
            title = sub_blog.xpath('a/text()').extract_first().strip()
            link = sub_blog.xpath('a/@href').extract_first()

            item['title'] = replace_special_chars(title)
            item['link'] = link
            
            #Make a request to actual link for the blog to extract other info
            # response =  requests.get(link).content
            request = scrapy.Request(link, callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request
            # self.parse_sub_blog(response)
        
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0

        # Find the actual article block
        main_block = response.xpath('//div[@class="post"]/*')
        
        index = 0
        if main_block[0].xpath('a/text()'):
            item['author'] = main_block[0].xpath('a/text()').extract_first()
            index = 1
        elif main_block[1].xpath('a/text()') and 'By ' in main_block[1].xpath('a/text()').extract_first():
            index = 2
            item['author'] = main_block[1].xpath('a/text()').extract_first()
        
        for block in main_block[index:]:
            block_string = block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        
        item['word_count'] = word_count
        item['date'] = response.xpath('//div[@class="navigation"]/p[1]').re(r'.*?: (.*?)<')[0]

        yield item

    # def parse(self, response):
    #     blog_posts = response.xpath('//td[@id]')
    #     for sub_blog in  blog_posts:
    #         item = BlogExtractItem()
    #         #Get Title, Link, Date
    #         title = sub_blog.xpath('a/text()').extract_first().strip()
    #         link = sub_blog.xpath('a/@href').extract_first()

    #         item['title'] = replace_special_chars(title)
    #         item['link'] = link
            
    #         #Make a request to actual link for the blog to extract other info
    #         request =  scrapy.Request(link, callback=self.parse_sub_blog, dont_filter=True)
    #         request.meta['dont_redirect'] = True
    #         request.meta['item'] = item
    #         yield request
        
    # def parse_sub_blog(self, response):
    #     print response.url
    #     item = response.meta['item']
    #     word_count = 0

    #     # Find the actual article block
    #     main_block = response.xpath('//div[@class="post"]/*')
    #     print response.text
    #     return
    #     item['author'] =  main_block[0].xpath('a/@text()').extract_first()
    
    #     for block in main_block[1:]:
    #         block_string = block.xpath('string()').extract()[0]
    #         word_count += get_word_count(block_string)
        
    #     item['word_count'] = word_count
    #     item['date'] = response.xpath('//div[@class="navigation"]/p[1]/text()')

    #     yield item


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
    



            