# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["neilpatel.com"]
    start_urls = ['https://neilpatel.com/blog/']
    page_number = 1

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//li[contains(@class, "type-post status-publish")]')
        if not blogs:
            return
        
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link
            title = sub_blog.xpath('a/h2/text()').extract_first()
            link = sub_blog.xpath('a/@href').extract_first()
            
            item['title'] = replace_special_chars(title)
            item['link'] = link

            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request

        next_page_url = self.start_urls[0] + 'page/' + str(self.page_number)
        yield scrapy.Request(next_page_url, callback=self.parse)
        self.page_number += 1
        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']

        date =  response.xpath('//meta[@property="article:published_time"]/@content').re(r'(.*?)T')
        if date:
            item['date'] = date[0]

        main_block = response.xpath('//div[@class="entry-content"]/*')
        continue_tags = ["smart-track-player stp-color-006cb5-006cb5 smart-track-player-dark"]
        word_count = 0
        for block in main_block:
            # if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in continue_tags:
                # continue
            block_string =  block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        item['word_count'] = word_count
        item['comments_count'] = response.xpath('//div[@class="comment-heading"]//span/text()').extract_first()

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