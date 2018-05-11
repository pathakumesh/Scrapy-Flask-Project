# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["budgetsaresexy.com"]
    start_urls = ['http://www.budgetsaresexy.com/']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//div[contains(@id, "post-")]')
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link, Date, Comment
            title = sub_blog.xpath('h2/a/text()').extract_first()
            link = sub_blog.xpath('h2/a/@href').extract_first()
            date = sub_blog.xpath('abbr[@class="teaser_date published"]/text()').extract_first()
            comments_count =  sub_blog.xpath('a[@class="teaser_comments"]/span/text()').extract_first()
            
            
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['date'] = date
            item['comments_count'] = comments_count
            
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request
        
        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(),"Older Posts")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
            
    def parse_sub_blog(self, response):
        item = response.meta['item']

        author = response.xpath('//span[@class="author vcard"]/span/text()').extract_first()
        item['author'] = author
        main_block = response.xpath('//div[@class="format_text entry-content"]/*')

        word_count = 0
        for block in main_block:
            if block.xpath('@class') and block.xpath('@class').extract()[0] in ["sw-pinit post_image alignnone", "nc_socialPanel swp_flatFresh swp_d_fullColor swp_i_fullColor swp_o_fullColor scale-100 scale-fullWidth swp_one"]:
                continue
            if block.xpath('@id') and block.xpath('@id').extract()[0] in ["tve_leads_end_content"]:
                break
            block_string =  block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        item['word_count'] = word_count - 5
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
            _line = re.sub(r'<img.*/>', '', _line)
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
    string = string.replace("\xe2\x80\x99", "'")
    string = string.replace("\xe2\x80\x9d", "\"").replace("\xe2\x80\x9c", "\"")
    string = string.replace("\xc2\xae", "®")
    string = string.replace("\xc2\xa0", " ")
    string = string.replace("\xe2\x80\xa6", "... ")
    
    return string