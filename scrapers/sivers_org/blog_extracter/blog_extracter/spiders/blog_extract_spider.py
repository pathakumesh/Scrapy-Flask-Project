# -*- coding: utf-8 -*-

import re
import scrapy
import scrapy_splash
from scrapy_splash import SplashRequest

import logging as log
from blog_extracter.items import BlogExtractItem


script = """
function main(splash)
    local scroll_to = splash:jsfunc("window.scrollTo")
    local get_body_height = splash:jsfunc(
        "function() {return document.body.scrollHeight;}"
    )
    assert(splash:go(splash.args.url))
    scroll_to(0, get_body_height())
    assert(splash:wait(5))
    return 
    {
        html = splash:html(),
    }
end"""
#splash.scroll_position = {100, 15000}

class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["sivers.org"]
    start_urls = ['https://sivers.org/blog']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//ul/*')
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link
            title = sub_blog.xpath('a/text()').extract_first()
            link = sub_blog.xpath('a/@href').extract_first()
            
            item['title'] = replace_special_chars(title)
            item['link'] = self.start_urls[0].split('/blog')[0] + link
    
            yield SplashRequest(item['link'], self.parse_sub_blog, 
                    endpoint = 'execute',
                    args={
                        'lua_source': script,
                        'pad': 32,
                        'css': 'a.title'
                    },
                    meta = {'item': item}
                
            )
            # yield item

        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']

        main_block = response.xpath('//article/*')
        date = main_block[0].xpath('small/text()').extract_first()
        item['date'] = date
        
        word_count = 0
        for block in main_block[1:-1]:
            block_string =  block.xpath('string()').extract()[0]
            if '<footer>' in block_string:
                break
            word_count += get_word_count(block_string)
        item['word_count'] = word_count

        comments_box = response.xpath('//li[contains(@id, "comment-")]')
        item['comments_count'] = len(comments_box) if comments_box else 0
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