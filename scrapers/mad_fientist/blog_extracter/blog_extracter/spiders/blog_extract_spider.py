# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["madfientist.com"]
    start_urls = ['https://www.madfientist.com/articles']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//div[@class= "col-md-9 col-sm-12"]')
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link
            title = sub_blog.xpath('h2/a/text()').extract_first()
            link = sub_blog.xpath('h2/a/@href').extract_first()
            comments_count = sub_blog.xpath('div[@class="entry-meta"]/a').re(r'(\d+)\s*Comment')
            
            
            
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['comments_count'] = comments_count[0] if comments_count else 0
            
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request

        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(),"Older posts")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']        
        
        main_block = response.xpath('//div[@class="entry-content"]/*')
        end_tag = ["page-link-box"]
        start_tag = ["padding:20px"]
        class_ignore_tag = ["ck_form ck_naked ck_horizontal"]
        type_ignore_tag = ["text/css"]
        word_count = 0
        for block in main_block:
            if block.xpath('@style').extract_first() and block.xpath("@style").extract_first() in start_tag:
                continue
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in class_ignore_tag:
                continue
            if block.xpath('@type').extract_first() and block.xpath("@type").extract_first() in type_ignore_tag:
                continue
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in end_tag:
                break
            
            if '<ul' in block.extract():
                for li_item in block.xpath('li'):
                    block_string = li_item.xpath('string()').extract()[0]
                    word_count += get_word_count(block_string)
                continue
            if block.xpath('string()').extract()[0] in ["Full Transcript", "Related Post"]:
                break
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

            
            _line = _line.replace(u'\xe2\x80\x9d', '')
            _line = _line.replace(u'\xe2\x80\x9c', '')
            _line = _line.replace(u'\u2026', ' ')
            _line = _line.replace('- ', ' ')
            _line = _line.replace('.', '')
            l_count += len(_line.split())
    
    return l_count

def replace_special_chars(string):
    #Proceed such that unicode characters are properly handled
    string = string.encode('utf-8')
    string = string.replace("\xe2\x80\x93", "-")
    string = string.replace("\xe2\x80\x94", "--")
    string = string.replace("\xe2\x80\x99", "'")
    string = string.replace("\xe2\x80\x9d", "\"").replace("\xe2\x80\x9c", "\"")
    string = string.replace("\xc2\xae", "®")
    string = string.replace("\xc2\xa0", " ")
    string = string.replace("\xe2\x80\xa6", "... ")
    
    return string