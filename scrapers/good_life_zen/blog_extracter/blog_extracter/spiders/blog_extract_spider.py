# -*- coding: utf-8 -*-

import re
import json
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["goodlifezen.com/"]
    start_urls = ["https://goodlifezen.com/"]
    intermediate_url = "https://goodlifezen.com/wp-admin/admin-ajax.php?action=thrive_load_more_latest_posts"
    page_num = 0
    exclude_posts = None

    def parse(self, response):
        if not self.exclude_posts:
            self.exclude_posts = response.xpath('//input[@id="tt-hidden-exclude-posts"]/@value').extract_first()
            print 'exclude_posts ', self.exclude_posts
        blogs = response.xpath('//div[@class="scc left"]')
        if not blogs:
            return
        
        for blog in blogs:
            item = BlogExtractItem()
            title = blog.xpath('div[@class="scbt"]/h5/a/text()').extract_first()
            link = blog.xpath('div[@class="scbt"]/h5/a/@href').extract_first()
            author = blog.xpath('div[@class="scbt"]/span/a/text()').extract_first().strip()
            item['title'] = title
            item['link'] = link
            item['author'] = author
            request =  scrapy.Request(link, callback=self.parse_sub_blog, dont_filter = True)
            request.meta['item'] = item
            yield request
    
        yield scrapy.FormRequest(
            url= self.intermediate_url,
            formdata={"page": str(self.page_num), "excludePosts": self.exclude_posts},
            callback=self.parse,
            dont_filter = True
        )
        self.page_num += 1



    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0
        
        ignore_rows = ["met", "fwit","nc_socialPanel swp_flatFresh swp_d_fullColor swp_i_fullColor swp_o_fullColor scale-100 scale-fullWidth swp_one"]
        rows =  response.xpath('//article/div[@class="awr"]/*')
        
        for row in rows:
            if row.xpath('@class').extract_first() and row.xpath("@class").extract_first() in ignore_rows:
                continue
            block_line =  row.xpath('string()').extract()[0]
            word_count += get_word_count(block_line)
        item['word_count'] = word_count
        
        comments_count = response.xpath('//div[@class= "awr cmm"]').re(r'\s*[>?](.*?)\s*comment')
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
            #remove bullets and special characters
            _line = re.sub(r'<img.*/>', '', _line)
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
    



            