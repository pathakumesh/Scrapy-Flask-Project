# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["scienceofrelationships.com"]
    start_urls = ['http://www.scienceofrelationships.com']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//div[@class="journal-entry"]')
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link, Date
            title = sub_blog.xpath('div[@class="journal-entry-text"]/h2/a/text()').extract_first()
            link = sub_blog.xpath('div[@class="journal-entry-text"]/h2/a/@href').extract_first()
            try:
                author = sub_blog.xpath('div[@class="journal-entry-tag journal-entry-tag-post-body"]\
                            /div/span[@class="posted-by"]/a/text()').extract()[1]
            except:
                author = sub_blog.xpath('div[@class="journal-entry-text"]/div[@class="journal-entry-tag journal-entry-tag-post-body"]\
                            /div/span[@class="posted-by"]/a/text()').extract()[1]
            try:
                date = sub_blog.xpath('div[@class="journal-entry-text"]/div[@class="journal-entry-tag journal-entry-tag-post-body"]\
                            /div/span[@class="posted-on"]/text()').extract()[1]
            except:
                date = sub_blog.xpath('div[@class="journal-entry-tag journal-entry-tag-post-body"]\
                            /div/span[@class="posted-on"]/text()').extract()[1]
            item['title'] = replace_special_chars(title)
            item['link'] = self.start_urls[0]+link
            
            item['author'] = author
            item['date'] = date
            
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            
            yield request
        
        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(),"Next 20 Entries")]')
        if next_page:
            next_page_url = self.start_urls[0]+next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0

        main_block = response.xpath('//div[@class="body"]/*')

        ignore_tags = ["https://onlinelibrary.wiley.com/doi/abs/10.1111/pere.12225", "http://www.dylanselterman.com",\
                        "http://psy.psych.colostate.edu/psylist/detail.asp?Num=47"]
        ignore_strings = ["Dylan Selterman","Jennifer Harman"]
        breaking_string = "Interested in learning more about relationships"

        word_count = 0
        for block in main_block:
            block_string = block.xpath('string()').extract()[0]
            if breaking_string in block_string:
                word_count += get_word_count(block_string.split(breaking_string)[0])
                break
            if any(s in block_string for s in ignore_strings):
                continue
            if block.xpath('a/@href').extract_first() in ignore_tags:
                continue

            if block.extract().startswith('<p><sup>1</sup>') or block.extract().startswith('<p><sup><span>1'):
                break

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
            _line = re.sub(r'<img.*/>', '', _line)
            _line = _line.replace('- ', ' ')
            #remove bullets and special characters
            _line = re.sub(u'\u25cf\t', '', _line)
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