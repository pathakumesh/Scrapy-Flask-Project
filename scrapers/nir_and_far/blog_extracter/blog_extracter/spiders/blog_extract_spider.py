# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem

from urllib import urlencode,quote, pathname2url
from scrapy.contrib.spiders import CrawlSpider, Rule



class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["nirandfar.com","disqus.com"]
    start_urls = ['https://www.nirandfar.com/blog']

    def parse(self, response):
        blog_posts = response.xpath('//article[contains(@class, "type-post status-publish")]')
        print 'page_url ', response.url
        for sub_blog in  blog_posts:
            item = BlogExtractItem()
            
            # get post_id which is needed to call another request to get comments
            post_id = sub_blog.xpath('@class')[0].re(r'post-(\w+)')[0]

            #Get Title, Link, Date
            title = sub_blog.xpath('h2[@class="entry-title"]/a/text()').extract_first().strip()
            link = sub_blog.xpath('h2[@class="entry-title"]/a/@href').extract_first()
            
                
            item['title'] = replace_special_chars(title)
            item['link'] = link

            # Make a request to actual link for the blog to extract other info
            request = scrapy.Request(link, callback=self.parse_sub_blog)
            request.meta['dont_redirect'] = True
            request.meta['item'] = item
            request.meta['post_id'] = post_id
            yield request
        
        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(),"Older Entries")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
        
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0

        date =  response.xpath('//meta[@property="article:published_time"]/@content').re(r'(.*?)T')
        item['date'] = date[0] if date else None


        # Find the actual article block
        main_block = response.xpath('//div[@class="entry-content"]/*')
        end_tag = ["tve_leads_end_content"]
        continue_tags = ["tve-leads-two-step-trigger tl-2step-trigger-2968",
                "tve-leads-post-footer tve-tl-anim tve-leads-track-post_footer-10 tl-anim-instant tve-leads-triggered"]
        word_count = 0
        for block in main_block:
            if block.xpath('@id').extract_first() and block.xpath("@id").extract_first() in end_tag:
                break
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in continue_tags:
                continue
            block_string = block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)

        residue_texts = response.xpath('//div[@class="entry-content"]/text()').extract()
        if residue_texts:
            block_string = ''.join(text.replace('\n', '. ') for text in residue_texts)
            word_count += get_word_count(block_string)
        
        item['word_count'] = word_count
        
        comments_url = get_comments_url(item['link'], item['title'], response.meta['post_id'])
        request = scrapy.Request(comments_url, callback=self.parse_comments)
        request.meta['item'] = item
        
        yield request


    def parse_comments(self, response):
        item = response.meta['item']
        item['comments_count'] = re.search(r'total":(\w+),', response.text).group(1)
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
    
    return string
    


def get_comments_url(link, title, post_id):
    title = title.replace('\xe2\x80\x99', '\'').replace('\xe2\x80\x98', '\'')\
            .replace('\xe2\x80\x9c', '\"').replace('\xe2\x80\x9d', '\"')\
            .replace('\xe2\x80\x94', '\--').replace('\xe2\x80\xa6', '...')\
            .replace('#', '%23')
    params =  {
        "base": "default",
        "f": "nirandfar",
        "t_u": link,
        "t_i": "%s https://www.nirandfar.com/?p=%s" % (post_id, post_id),
        "t_e": title,
        "t_d": title,
        "t_t": title,
        "s_o": "default"
    }
    try:
        comments_url = "https://disqus.com/embed/comments/?" + '&'.join("%s=%s" % (k,v) for k,v in params.iteritems()) +"#version=c0193bf9d4406245bd1c5f08cc4b86c6"
    except:
        print "EXCEPTION for link: "
        print link
        print title
        print post_id
        return "https://disqus.com/embed/comments/?"
    if link =="":
        print comments_url
    return comments_url




            