# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem
from urllib import quote_plus


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["leonlogothetis.com", "facebook.com"]
    start_urls = ['http://www.leonlogothetis.com/blog/']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//div[@class="post"]')
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link
            link = sub_blog.xpath('a/@href').extract_first()
            title = sub_blog.xpath('a/span/span[@class="title"]/strong/text()').extract_first()
            date = sub_blog.xpath('a/span/span[@class="date"]/em/text()').extract_first()
            
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['date'] = date
            
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            request.meta['dont_redirect'] = True
            yield request

        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//span[contains(text(),"Older posts")]')
        if next_page:
            next_page_url = next_page.xpath('../@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        
        main_block = response.xpath('//div[@class="entry-content"]/*')
        ignore_tags = ["blogtitle"]
        word_count = 0
        for block in main_block:
            if block.xpath('a/@href').extract_first() and block.xpath('a/@href').extract_first() == 'http://www.leonlogothetis.com/books/':
                break
            block_string =  block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        item['word_count'] = word_count
        api_key = response.xpath('//meta[@property="fb:app_id"]/@content').extract_first()
        comments_url = get_comments_url(api_key, item['link'])
    
        request = scrapy.Request(comments_url, callback=self.parse_comments)
        request.meta['item'] = item
        yield request

    def parse_comments(self, response):
        item = response.meta['item']
        item['comments_count'] = re.search(r'totalCount":(\w+),', response.text).group(1)
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

def get_comments_url(api_key, link):

    params = {
        "api_key": api_key,
        "channel_url": "http://staticxx.facebook.com/connect/xd_arbiter/r/FdM1l_dpErI.js?version=42#cb=f2a9326f9603f7&domain=www.leonlogothetis.com&origin=http%3A%2F%2Fwww.leonlogothetis.com%2Ffe3cfb6c69d898&relation=parent.parent",
        "colorscheme": "light",
        "href": link,
        "locale": "en_US",
        "numposts": "5",
        "sdk": "joey",
        "skin": "light",
        "version": "v2.3",
        "width": "100%"
    }

    comments_url = "https://www.facebook.com/plugins/feedback.php?" + '&'.join("%s=%s" % (k,v) for k,v in params.iteritems())
    
    return comments_url