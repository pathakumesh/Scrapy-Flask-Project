# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["sidehustlenation.com"]
    start_urls = ['https://www.sidehustlenation.com/blog/']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//header[@class="entry-header"]')
        for sub_blog in blogs:
            
            item = BlogExtractItem()
            #Get Title, Link
            title = sub_blog.xpath('h2/a/text()').extract_first()
            link = sub_blog.xpath('h2/a/@href').extract_first()
            date = sub_blog.xpath('div/span/a/time[@class="entry-date published"]/text()').extract_first()
            
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['date'] =date
            
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request
            # yield item
        
        # # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[@class="next page-numbers"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        
        main_block = response.xpath('//div[@class="entry-content"]/*')
        word_count = 0
        continue_class_tags = ['nc_socialPanel swp_flatFresh swp_d_fullColor swp_i_fullColor swp_o_fullColor scale-100 scale-fullWidth swp_one']
        continue_id_tags = ["adcp-wrapper"]
        end_class_tag = "nc_socialPanel swp_flatFresh swp_d_fullColor swp_i_fullColor swp_o_fullColor scale-100 scale-fullWidth swp_three"
        for block in main_block:
            
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in continue_class_tags:
                continue
            
            if block.xpath('@id').extract_first() and block.xpath("@id").extract_first() in continue_id_tags:
                continue
            
            if block.xpath('@id').extract_first() and block.xpath("@id").extract_first() in end_class_tag:
                break

            block_string =  block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        item['word_count'] = word_count - 10
        
        item['author'] =  response.xpath('//meta[@property="article:author"]/@content').extract_first()
        
        comments_count = response.xpath('//h3[@class="comments-title"]').re(r'.*?(\d+)\s*thought')
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
            _line = re.sub(r'Photo Credit: \S+.(com|au)', '', _line)
            _line = re.sub(r'<img.*?>', '', _line)
            _line = re.sub(u'\u25cf\t', '', _line)
            _line = re.sub(u'\u2013', '-', _line)
            _line = re.sub(u'\u2014', '- ', _line)

            
            _line = _line.replace(u'\xe2\x80\x9d', '')
            _line = _line.replace(u'\xe2\x80\x9c', '')
            _line = _line.replace(u'\u2026', ' ')
            _line = _line.replace('- ', ' ')
            _line = _line.replace('. ', ' ')
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