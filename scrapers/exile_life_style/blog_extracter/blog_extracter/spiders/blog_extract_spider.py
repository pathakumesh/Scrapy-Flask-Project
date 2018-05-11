# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["exilelifestyle.com"]
    start_urls = ['http://exilelifestyle.com/archive/']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//h3[contains(text(), "Monthly Archive")]/following-sibling::ul/*')
        # print response.text 
        for sub_blog in blogs:
            monthly_link =  sub_blog.xpath('a/@href').extract_first()
            # Make a request to actual link for the blog to extract other info
            yield  scrapy.Request(monthly_link, callback=self.parse_monthly_blog)
            
    def parse_monthly_blog(self, response):
        blogs = response.xpath('//ul[@class="posts-archive"]/li')
        for blog in blogs:
            
            item = BlogExtractItem()
            
            title = blog.xpath('div/h2/a/text()').extract_first().strip()
            link = blog.xpath('div/h2/a/@href').extract_first()
            
            item['title'] = replace_special_chars(title)
            item['link'] = link
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request


    def parse_sub_blog(self, response):
        item = response.meta['item']
        
        item['date'] = response.xpath('//span[@class="entry-date"]/text()').extract_first()

        main_block = response.xpath('//section[@class="entry-content"]/*')
        word_count = 0
        for block in main_block:
            block_string =  block.xpath('string()').extract()[0]
        
            word_count += get_word_count(block_string)

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
            if _line == 'back to top':
                break
            #remove bullets and special characters
            _line = re.sub(r'Photo Credit: \S+.(com|au)', '', _line)
            _line = re.sub(r'<img.*>', '', _line)
            _line = re.sub(u'\u25cf\t', '', _line)
            _line = re.sub(u'\u2013', '-', _line)
            _line = re.sub(u'\u2014', '- ', _line)
            _line = _line.replace('- ', ' ')
            _line = _line.replace('.', '')
            l_count += len(_line.split())
    
    return l_count

def replace_special_chars(string):
    #Proceed such that unicode characters are properly handled
    string = string.encode('utf-8')
    string = string.replace("\xe2\x80\x93", "-")
    string = string.replace("\xe2\x80\x99", "'")
    string = string.replace("\xe2\x80\x9d", "\"").replace("\xe2\x80\x9c", "\"")
    string = string.replace("\xc2\xae", "®")
    string = string.replace("\xc2\xa0", " ")
    string = string.replace("\xe2\x80\xa6", "... ")
    
    return string