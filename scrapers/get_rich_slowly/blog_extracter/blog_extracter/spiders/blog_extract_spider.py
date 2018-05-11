# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem

class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["getrichslowly.org"]
    start_urls = ['https://www.getrichslowly.org/archives/']

    def parse(self, response):
        archive_list = response.xpath('//div[@id="smart-archives-list"]/ul[@class="archive-list"]')
        print response.url
        # print response.text
        for sub_block in  archive_list:
            for each_blog in sub_block.xpath('li'): 
                # print each_blog
                item = BlogExtractItem()
                # #Get Title, Link, Date
                title = each_blog.xpath('a/text()').extract_first().strip()
                link = each_blog.xpath('a/@href').extract_first()
                date = each_blog.re(r'.*?(\d+\s*\w+\s*\d+)\s*-')[0]
                comments_count = each_blog.re(r'.*?\((\d+)\s*comment')[0]

                item['title'] = replace_special_chars(title)
                item['link'] = link
                item['date'] = date
                item['comments_count'] = comments_count
            
                # Make a request to actual link for the blog to extract other info
                request =  scrapy.Request(link, callback=self.parse_sub_blog)
                request.meta['dont_redirect'] = True
                request.meta['item'] = item
                yield request

        
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0
        
        item['author'] = response.xpath('//span[@class="entry-author-name"]/text()').extract_first()
        # Find the actual article block
        main_block = response.xpath('//div[@class="entry-content"]/*')
        
        ignore_blocks = ["getri-before-content", "nc_socialPanel swp_flatFresh swp_d_fullColor swp_i_fullColor swp_o_fullColor scale-100 scale-fullWidth swp_one",\
                        "wwsgd", "nc_socialPanel swp_flatFresh swp_d_fullColor swp_i_fullColor swp_o_fullColor scale-100 scale-fullWidth swp_one nc_floater swp_two",\
                        "nc_socialPanel swp_flatFresh swp_d_fullColor swp_i_fullColor swp_o_fullColor scale-100 scale-fullWidth swp_three"]
        word_count = 0
        for block in main_block:
            if block.xpath('@class') and block.xpath('@class').extract()[0] in ignore_blocks:
                continue
            block_string = block.xpath('string()').extract()[0]
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
    



            