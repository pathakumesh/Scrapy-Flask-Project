# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["iwillteachyoutoberich.com"]
    start_urls = ['https://www.iwillteachyoutoberich.com/blog/']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//div[@class="article"]')
        # print response.text 
        for sub_blog in blogs:
            item = BlogExtractItem()
            #Get Title, Link
            title = sub_blog.xpath('div[@class="top"]/h2/a/text()').extract_first()
            link = sub_blog.xpath('div[@class="top"]/h2/a/@href').extract_first()
            
            item['title'] = replace_special_chars(title)
            item['link'] = self.start_urls[0] + link.split("blog/")[1]
            
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request
            
        
        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//ul[contains(@class,"pagination responsive")]/li[@class="active"]/following-sibling::li')
        if next_page:
            url = next_page.xpath('a/@href').extract_first()
            next_page_url = self.start_urls[0] + url.split("blog/")[1]
            yield scrapy.Request(next_page_url, callback=self.parse)
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        
        main_block = response.xpath('//div[@class="entry-content"]/*')
        word_count = 0
        header = response.xpath('//p[@class="metadesc"]/text()').extract()
        for h in header:
            word_count += get_word_count(h)
        
        main_block = response.xpath('//div[@class="entry"]/*')
        
        if not main_block:
            main_block = response.xpath('//div[@class="col-md-8"]/*')
        
        if not main_block:
            main_block = response.xpath('//div[@class="col-md-8 col-md-offset-2"]/*')

        ignore_tags = ['marginTop-l padding-m borderRadius-s bg-exhaust scheme-light ',
                        'social-share counted marginTop-xl marginBottom-l col-md-11',
                        'fve-video-wrapper fve-image-embed fve-thumbnail-image youtube']
        for block in main_block:
            if 'iframe' in block.extract():
                continue
            if block.xpath('noscript'):
                continue
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in ignore_tags:
                continue
            block_string =  block.xpath('string()').extract()[0]
        
            word_count += get_word_count(block_string)
        for block in  response.xpath('//div[@class="entry"]/text()').extract():
            word_count += get_word_count(block)

        item['word_count'] = word_count
        
        date =  response.xpath('//meta[@property="article:published_time"]/@content').re(r'(.*?)T')
        if date:
            item['date'] = date[0]

        author =  response.xpath('//p[@class="by"]/a/text()').extract_first()
        if author:
            item['author'] = author.strip()
        comments_count = response.xpath('//h3[@class="text-center" and contains(text(), "Comments")]').re(r'(\d+)\s*Comment')
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
            _line = re.sub(u'\u2014', '- ', _line)
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