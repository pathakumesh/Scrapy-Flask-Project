# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["thewildwong.com"]
    start_urls = ['https://www.thewildwong.com/lastest-posts/']

    def parse(self, response):
        content = response.xpath('//div[@id="left-area"]')
        for sub_blog in  content.xpath('article'):
            item = BlogExtractItem()
            
            #Get Title, Link, Date
            title = sub_blog.xpath('h2[@class="entry-title"]/a/text()').extract_first()
            link = sub_blog.xpath('h2[@class="entry-title"]/a/@href').extract_first()
            author = sub_blog.xpath('p[@class="post-meta"]/span[@class="author vcard"]/a/text()').extract_first()
            date = sub_blog.xpath('p[@class="post-meta"]/span[@class="published"]/text()').extract_first()
            comments_count = sub_blog.xpath('p[@class="post-meta"]/span[@class="comments-number"]').re(r'(\d+)\s*comment')[0]
            
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['author'] = author
            item['date'] = date
            item['comments_count'] = comments_count

            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(link, callback=self.parse_sub_blog)
            request.meta['item'] = item
            
            yield request
        
        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(), "Older Entries")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0

        # Find the actual article block
        article =  response.xpath('//div[@class= "et_pb_text_inner"]/*')
        if not article:
            article =  response.xpath('//div[@class= "entry-content"]/*')
        ignore_blocks = ["mailmunch-forms-widget-304694", "mailmunch-forms-short-code mailmunch-forms-widget-303663","mailmunch-forms-after-post"]
        for div in article:
    
            #exclude unnecessary divs
            if div.xpath('@id') and div.xpath('@id').extract()[0]=="ts-fab-below":
                continue
            if div.xpath('@class') and div.xpath('@class').extract()[0] in ignore_blocks:
                continue
          
            #Extract the plain text and count the words
            div_line = div.xpath('string()').extract()[0]
            word_count += get_word_count(div_line)        
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
            #Remove twitter clickable text link
            _line = _line.replace('Click To Tweet', '')
            #remove bullets and special characters
            _line = re.sub(u'\u25cf\t', '', _line)
            
            #remove img tags
            _line = re.sub(r'<img.*/>', '', _line)
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
    



            