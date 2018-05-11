# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["bengreenfieldfitness.com"]
    start_urls = ['https://bengreenfieldfitness.com/article/']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//h1[@class="entry-title"]')
        for sub_blog in blogs:
            if sub_blog.xpath('span[text()="Articles"]'):
                continue
            if sub_blog.xpath('a[contains(text(),"The Weekly Roundup")]'):
                continue
            
            item = BlogExtractItem()
            #Get Title, Link
            title = sub_blog.xpath('a/text()').extract_first()
            link = sub_blog.xpath('a/@href').extract_first()
            
            item['title'] = replace_special_chars(title)
            item['link'] = link
            
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request
            # yield item
        
        # # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//div[@class="basel-pagination"]/span[@class="current"]/following-sibling::a')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        
        main_block = response.xpath('//div[@class="entry-content"]/*')
        word_count = 0
        ignore_tags = ['bengr-after-content','bengr-7-from-top', 'pdfemb-viewer']
        for block in main_block:
            if 'iframe' in block.extract():
                continue
            if block.xpath('noscript'):
                continue
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in ignore_tags:
                continue
            block_string =  block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        item['word_count'] = word_count
        
        # date_section = response.xpath('//div[@class="post-date"]')
        # if date_section:
            # day = date_section.xpath('span[@class="post-date-day"]/text()').extract_first().strip()
            # month = date_section.xpath('span[@class="post-date-month"]/text()').extract_first().strip()
            # item['date'] =  "%s %s" % (day,month)
        item['date'] =  response.xpath('//meta[@property="article:published_time"]/@content').re(r'(.*?)T')[0]
        item['author'] =  response.xpath('//li[@class="meta-author"]/a/text()').extract_first().strip()
        comments_count = response.xpath('//h2[@class="comments-title"]').re(r'.*?(\d+)\s*thought')
        item['comments_count'] = comments_count[0] if comments_count else 0
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
    string = string.replace("\xc2\xa0", " ")
    string = string.replace("\xe2\x80\xa6", "... ")
    
    return string