# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem

from urllib import urlencode,quote, pathname2url
from scrapy.contrib.spiders import CrawlSpider, Rule



class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["negharfonooni.com","disqus.com"]
    start_urls = ['http://www.negharfonooni.com/blog/']

    def parse(self, response):
        blog_posts = response.xpath('//div[contains(@class, "type-post status-publish")]')
        print 'page_url ', response.url
        for sub_blog in  blog_posts:
            item = BlogExtractItem()
            
            # get post_id which is needed to call another request to get comments
            post_id = sub_blog.xpath('@class')[0].re(r'\s*post-(\d+)\s*')[0]            

            #Get Title, Link, Date
            title = sub_blog.xpath('div[@class="blog-post-wrap"]//h2[@class="blog-post-title"]/a/text()').extract_first().strip()
            link = sub_blog.xpath('div[@class="blog-post-wrap"]//h2[@class="blog-post-title"]/a/@href').extract_first().strip()
            
            date = sub_blog.xpath('div[@class="blog-post-wrap"]//span[@class="vntd-meta-date"]/span/text()').extract_first().strip()
            author = sub_blog.xpath('div[@class="blog-post-wrap"]//span[@class="vntd-meta-author"]/a/text()').extract_first().strip()
            disgus_identifier = sub_blog.xpath('div[@class="blog-post-wrap"]//span[@class="dsq-postid"]/@data-dsqidentifier').extract_first().strip()
                
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['date'] = date
            item['author'] = author
            
            # Make a request to actual link for the blog to extract other info
            request = scrapy.Request(link, callback=self.parse_sub_blog)
            request.meta['dont_redirect'] = True
            request.meta['item'] = item
            request.meta['disgus_identifier'] = disgus_identifier
            yield request
        
        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(), "Next")]')
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
        main_block = response.xpath('//div[@class="blog-post-content-wrap"]/*')
        
        ignore_blocks = ["wp-post-navigation"]
        word_count = 0
        for block in main_block:
            if block.xpath('@class') and block.xpath('@class').extract()[0] in ignore_blocks:
                continue
            block_string = block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        
        item['word_count'] = word_count
        
        comments_url = get_comments_url(item['link'], item['title'], response.meta['disgus_identifier'])
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
    


def get_comments_url(link, title, disgus_identifier):
    title = title.replace('\xe2\x80\x99', '\'').replace('\xe2\x80\x98', '\'')\
            .replace('\xe2\x80\x9c', '\"').replace('\xe2\x80\x9d', '\"')\
            .replace('\xe2\x80\x94', '\--').replace('\xe2\x80\xa6', '...')
    params =  {
        "base": "default",
        "f": "negharfonooni",
        "t_u": link,
        "t_i": disgus_identifier,
        "t_e": title,
        "t_d": title + " - Neghar Fonooni",
        "t_t": title,
        "s_o": "default"
    }
    try:
        comments_url = "https://disqus.com/embed/comments/?" + '&'.join("%s=%s" % (k,v) for k,v in params.iteritems()) +"#version=90b177d97dda66d90b9275eb687a8640"
    except:
        print "EXCEPTION for link: "
        print link
        print title
        print data-dsqidentifier
        return "https://disqus.com/embed/comments/?"
    return comments_url




            