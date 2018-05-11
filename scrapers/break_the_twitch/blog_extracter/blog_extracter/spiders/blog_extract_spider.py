# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


from scrapy.contrib.spiders import Rule


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["breakthetwitch.com"]
    start_urls = ['https://www.breakthetwitch.com/archives/']

    def parse(self, response):
        archives = response.xpath('//ul[@class="years"]/*')
        for year_block in  archives:
            _year = year_block.xpath('h2/text()').extract_first()
            
            month_block = year_block.xpath('ul[@class="months"]/*')
            for each_month in month_block:
                _month = each_month.xpath('h3/text()').extract_first()
            
                posts_for_month = each_month.xpath('ul[@class="posts"]/*')
                for post in posts_for_month:
                    item = BlogExtractItem()

                    _day,title =  post.xpath('string()').re(r'(\d+)\s+(.*)')
                    link = post.xpath('a/@href').extract_first()
                    item['title'] = title
                    item['link'] = link
                    item['date'] = "%s-%s-%s" % (_year, _month, _day)
    
                    #Make a request to actual link for the blog to extract other info
                    request =  scrapy.Request(link, callback=self.parse_sub_blog)
                    request.meta['dont_redirect'] = True
                    request.meta['item'] = item
                    yield request
                
    def parse_sub_blog(self, response):
        item = response.meta['item']
        
        item['author'] = response.xpath('//span[@class="entry-author-name"]/text()').extract_first()

        # Find the actual article block
        main_block = response.xpath('//div[@class="entry-content"]/*')
        ignore_blocks = ["apss-social-share apss-theme-1  clearfix", "entry-footer"]
        
        word_count = 0
        
        for block in main_block:
            if block.xpath('@class') and block.xpath('@class').extract()[0] in ignore_blocks:
                continue
            block_string = block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        
        item['word_count'] = word_count

        comments = response.xpath('//div[@class="entry-comments"]')
        comments_count = len(comments.xpath('ol[@class="comment-list"]/li')) if comments else 0
        item['comments_count'] = comments_count

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