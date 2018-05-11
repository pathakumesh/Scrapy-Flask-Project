# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["makingsenseofcents.com"]
    start_urls = ['https://www.makingsenseofcents.com/blog']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//header[@class="entry-header"]')
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link
            title = sub_blog.xpath('h2/a/text()').extract_first()
            link = sub_blog.xpath('h2/a/@href').extract_first()
            date = sub_blog.xpath('p[@class="entry-meta"]/time/text()').extract_first().strip()
            author = sub_blog.xpath('p[@class="entry-meta"]/span[@class="entry-author"]/span/text()').extract_first().strip()
            comments_count = sub_blog.xpath('p[@class="entry-meta"]/span[@class="entry-comments-link"]/a').re(r'(\d+)\s*Comment')
            
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['date'] = date
            item['author'] = author
            item['comments_count'] = comments_count[0] if comments_count else None

            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request

        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(),"Next Page")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']

        main_block = response.xpath('//div[@class="entry-content"]/*')
        
        continue_class_tags = ["nc_socialPanel swp_flatFresh swp_d_fullColor swp_i_fullColor swp_o_fullColor scale-100 scale-fullWidth swp_one",
                "ck_form_container ck_inline","wp_rp_wrap  wp_rp_vertical_m",
                "nc_socialPanel swp_flatFresh swp_d_fullColor swp_i_fullColor swp_o_fullColor scale-100 scale-fullWidth swp_three"]
        continue_style_tags = ["float: none; margin:10px 0 10px 0; text-align:center;",
                    "font-size: 0px; height: 0px; line-height: 0px; margin: 0; padding: 0; clear: both;"]
        continue_language_tags = ["JavaScript"]
        word_count = 0
        for block in main_block:
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in continue_class_tags:
                continue
            if bool(set(block.xpath('descendant::div/@class').extract()) & set(continue_class_tags)):
                continue
            if bool(set(block.xpath('descendant::script/@language').extract()) & set(continue_language_tags)):
                continue
            if block.xpath('@style').extract_first() and block.xpath("@style").extract_first() in continue_style_tags:
                continue
            if block.extract().startswith('<ul'):
                for li_item in block.xpath('li'):
                    block_string = li_item.xpath('string()').extract()[0]
                    word_count += get_word_count(block_string)
                continue
            block_string =  block.xpath('string()').extract()[0]
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