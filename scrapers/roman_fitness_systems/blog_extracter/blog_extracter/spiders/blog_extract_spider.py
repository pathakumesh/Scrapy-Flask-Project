# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector

class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["romanfitnesssystems.com"]
    start_urls = ['http://romanfitnesssystems.com/articles/']

    def parse(self, response):
        blog_posts = response.xpath('//div[@class="blog-posts"]')
        print response.url
        for sub_blog in  blog_posts.xpath('div[@class="blog-post"]/div[@class="blog-post__description"]'):
            item = BlogExtractItem()
            #Get Title, Link, Date
            title = sub_blog.xpath('h2/a/text()').extract_first().strip()
            link = sub_blog.xpath('h2/a/@href').extract_first()
            author = sub_blog.xpath('div[@class="blog-post__meta"]/strong/a/text()').extract_first()

            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['author'] = author
            
            #Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(link, callback=self.parse_sub_blog)
            request.meta['dont_redirect'] = True
            request.meta['item'] = item
            yield request
        
        #If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(@title, "Next Page")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            request = scrapy.Request(next_page_url, callback=self.parse)
            request.meta['dont_redirect'] = True
            request.meta['handle_httpstatus_all'] = True
            yield request
        
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0

        # Find the actual article block
        main_block = response.xpath('//div[@class="teach-me-bro hb-content"]/*')
        
        ignore_blocks = ["mceMediaCreditOuterTemp alignright", "share-this-post", "author-info"]
        word_count = 0
        for block in main_block:
            if block.xpath('@class') and block.xpath('@class').extract()[0] == 'comments':
                item['comments_count'] = len(block.xpath('//ul[@id="post-comments"]/li'))
                continue
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
    



            