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
    allowed_domains = ["marcandangel.com"]
    start_urls = ['http://www.marcandangel.com/']

    def parse(self, response):
        blog_posts = response.xpath('//main[@class="content"]')
        print 'next_page_url ', response.url
        for sub_blog in  blog_posts.xpath('article[contains(@class, "post-")]'):
            item = BlogExtractItem()
            

            #Get Title, Link, Date
            title = sub_blog.xpath('header/h2[@class="entry-title"]/a/text()').extract_first()
            if not title:
                title = sub_blog.xpath('header/h2[@class="entry-title"]/a/strong/text()').extract_first()
            title = title.strip()
            link = sub_blog.xpath('header/h2[@class="entry-title"]/a/@href').extract_first()
            date = sub_blog.xpath('header/p[@class="entry-meta"]/time/text()').extract_first().strip()
            author = sub_blog.xpath('header/p[@class="entry-meta"]/span[@class="entry-author"]/span/text()').extract_first().strip()
            comments_count = sub_blog.xpath('header/p[@class="entry-meta"]/span[@class="entry-comments-link"]/a').re(r'(\d+)\s*Comment')
            item['comments_count'] = comments_count[0] if comments_count else 0
                
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['date'] = date
            item['author'] = author
            
            
            # Make a request to actual link for the blog to extract other info
            request = scrapy.Request(link, callback=self.parse_sub_blog)
            request.meta['dont_redirect'] = True
            request.meta['item'] = item
            yield request
        
        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(), "Next Page")]')
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
        main_block = response.xpath('//div[@class="entry-content"]/*')
        
        ignore_blocks = ["share-after share-filled share-small"]
        word_count = 0
        for block in main_block:
            if block.xpath('@class') and block.xpath('@class').extract()[0] in ignore_blocks:
                break
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
            if _line == 'back to top':
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
    



            