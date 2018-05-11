# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["earlyretirementextreme.com"]
    start_urls = ['http://earlyretirementextreme.com/']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//div[@id="post-entry"]/div[@class="post-meta"]')
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link
            title = sub_blog.xpath('h1/a/text()').extract_first()
            link = sub_blog.xpath('h1/a/@href').extract_first()
            posted_date = sub_blog.xpath('div[@class="post-date"]').re(r'.*on\s*(.*)\s*<')
            author =sub_blog.xpath('div[@class="authors-cat"]/a[@rel="author"]/text()').extract_first()
            comments_count = sub_blog.xpath('div[@class="post-commented"]/a').re(r'(\d+)\s*Comment')
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['date'] = posted_date[0] if posted_date else None
            item['author'] = author
            item['comments_count'] = comments_count[0] if comments_count else None

            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request

        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(),"Older Entries")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']

        main_block = response.xpath('//div[@class="post-content"]/*')
        ignore_tags = ["border:thin dotted black; padding:3mm;"]
        word_count = 0
        for block in main_block:
            if block.xpath('@style').extract_first() and block.xpath("@style").extract_first() in ignore_tags:
                continue
            if block.xpath('@id').extract_first() and block.xpath("@id").extract_first() == "bte_opp":
                break
            block_string =  block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        item['word_count'] = word_count - 200
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