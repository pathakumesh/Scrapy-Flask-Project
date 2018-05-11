# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["rosstraining.com"]
    start_urls = ['http://rosstraining.com/blog/']

    def parse(self, response):
        articles = response.xpath('//main[@id="main"]/article')
        print 'next_page_url ', response.url
        for sub_blog in articles:
            item = BlogExtractItem()
            header = sub_blog.xpath('div/header[@class="entry-header clear"]')

            #Get Title, Link, Date
            title = header.xpath('h1/a/text()').extract_first()
            link = header.xpath('h1/a/@href').extract_first()
            
            item['title'] = replace_special_chars(title)
            item['link'] = link
            meta_data = header.xpath('div[@class="entry-meta"]')
            
            author = meta_data.xpath('span/span[@class="author vcard"]/a/text()').extract_first()
            date = meta_data.xpath('span/a/time[@class="entry-date published"]/text()').extract_first()
            comment = meta_data.xpath('span[@class="comments-link"]/a').re(r'(\d+)\s*Comment')
            item['comments_count'] = comment[0] if comment else 0
            item['author'] = author
            item['date'] = date
            
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(link, callback=self.parse_sub_blog)
            request.meta['item'] = item
            
            yield request
        
        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[@class="next page-numbers"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0

        main_block = response.xpath('//div[@class="entry-content"]/*')
        
        ignore_blocks = list()
        continuing_strings = ['+++++']
        breaking_strings = ['Please like & share:', '(adsbygoogle']
        
        word_count = 0
        for block in main_block:
            
            if block.xpath('@class') and block.xpath('@class').extract()[0] in ignore_blocks:
                continue
            
            block_string = block.xpath('string()').extract()[0]
            
            if any(s in block_string for s in continuing_strings):
                continue
            
            if any(s in block_string for s in breaking_strings):
                ignore_blocks.append('BREAK')
                break
            word_count += get_word_count(block_string)
        if not ignore_blocks:
            print 'BREAKING...'
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
    



            