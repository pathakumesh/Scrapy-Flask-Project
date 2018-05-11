# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["jamesaltucher.com", "disqus.com"]
    start_urls = ['https://jamesaltucher.com/']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//div[@class="eight columns post-group-content"]/article')
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link
            title = sub_blog.xpath('header/h1/a/text()').extract_first()
            link = sub_blog.xpath('header/h1/a/@href').extract_first()
            date = sub_blog.xpath('footer//li[@class="date"]/time/text()').extract_first().strip()
            author = sub_blog.xpath('footer//li[@class="author"]').re(r'.*By\s*(.*?)\s*<')
            disgus_identifier = sub_blog.xpath('footer//li[@class="comments"]/a/span/@data-dsqidentifier').extract_first().strip()
        
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['date'] = date
            item['author'] = author[0] if author else None
        
        
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            request.meta['disgus_identifier'] = disgus_identifier
            yield request

        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(),"Older Entries")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']

        main_block = response.xpath('//section[@class="post-content clearfix"]/*')
        continue_tags = ["podcast-buttons-wrapper clearfix", "smart-track-player stp-color-00aeef-EEEEEE",
                        "openxzone large_openx", "openxzone incontent"]
        word_count = 0
        for block in main_block:
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in continue_tags:
                continue
            block_string =  block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        item['word_count'] = word_count

        comments_url = get_comments_url(item['link'], item['title'], response.meta['disgus_identifier'])
        request = scrapy.Request(comments_url, callback=self.parse_comments)
        request.meta['item'] = item
        
        yield request

    def parse_comments(self, response):
        item = response.meta['item']
        comments = re.search(r'total":(\w+),', response.text)
        item['comments_count'] = comments.group(1) if comments else 0
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

def get_comments_url(link, title, disgus_identifier):
    title = title.replace('\xe2\x80\x99', '\'').replace('\xe2\x80\x98', '\'')\
            .replace('\xe2\x80\x9c', '\"').replace('\xe2\x80\x9d', '\"')\
            .replace('\xe2\x80\x94', '\--').replace('\xe2\x80\xa6', '...')
    params =  {
        "base": "default",
        "f": "altucherconfidential",
        "t_u": link,
        "t_i": disgus_identifier,
        "t_e": title,
        "t_d": title + " - Altucher Confidential",
        "t_t": title,
        "s_o": "default"
    }
    try:
        comments_url = "https://disqus.com/embed/comments/?" + '&'.join("%s=%s" % (k,v) for k,v in params.iteritems()) +"#version=0c224241a140a6ab1eaaa8366f477ea8"
    except:
        return "https://disqus.com/embed/comments/?"
    return comments_url
