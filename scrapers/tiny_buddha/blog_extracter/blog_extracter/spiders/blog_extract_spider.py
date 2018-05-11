# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem

from urllib import urlencode,quote, pathname2url
from scrapy.contrib.spiders import CrawlSpider, Rule



class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["tinybuddha.com","disqus.com"]
    start_urls = ['https://tinybuddha.com/blog-posts/']

    def parse(self, response):
        blog_posts = response.xpath('//div[@id="content"]')
        print 'page_url ', response.url
        for sub_blog in  blog_posts.xpath('div[contains(@id, "post-")]'):
            item = BlogExtractItem()
            
            # get post_id which is needed to call another request to get comments
            post_id = sub_blog.xpath('@id')[0].re(r'post-(\w+)')[0]            
            
            #Get Title, Link, Date
            sub_block = sub_blog.xpath('div[@class="entry-content archive-content"]')
            if sub_block:
                title = sub_block.xpath('h2/a/@title').extract_first().strip()
                link = sub_block.xpath('h2/a/@href').extract_first()
                author = sub_block.xpath('div/a[@rel="author"]/text()').extract_first()
                
                item['title'] = replace_special_chars(title)
                item['link'] = link
                item['author'] = author
            
                # Make a request to actual link for the blog to extract other info
                request = scrapy.Request(link, callback=self.parse_sub_blog)
                request.meta['dont_redirect'] = True
                request.meta['item'] = item
                request.meta['post_id'] = post_id
                yield request
        
        #If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[@class = "nextpostslink"]')
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
        main_block = response.xpath('//div[@class="entry-content single-content extra"]/*')
        
        ignore_blocks = ["wp-biographia-container-around", "announcement"]
        word_count = 0
        for block in main_block:
            if block.xpath('@class') and block.xpath('@class').extract()[0] in ignore_blocks:
                continue
            if '<script>' in block.extract():
                continue  
            block_string = block.xpath('string()').extract()[0]
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
    


def get_comments_url(link, title, post_id):
    title = title.replace('\xe2\x80\x99', '\'').replace('\xe2\x80\x98', '\'')\
            .replace('\xe2\x80\x9c', '\"').replace('\xe2\x80\x9d', '\"')\
            .replace('\xe2\x80\x94', '\--').replace('\xe2\x80\xa6', '...')
    params =  {
        "base": "default",
        "f": "tinybuddha",
        "t_u": link,
        "t_i": "%s https://tinybuddha.com/?p=%s" % (post_id, post_id),
        "t_e": title,
        "t_d": title,
        "t_t": title,
        "s_o": "default"
    }
    try:
        comments_url = "https://disqus.com/embed/comments/?" + '&'.join("%s=%s" % (k,v) for k,v in params.iteritems()) +"#version=341c6ac006cf1e349b79ef1033b8b11a"
    except:
        print "EXCEPTION for link: "
        print link
        print title
        print post_id
        return "https://disqus.com/embed/comments/?"
    return comments_url




            