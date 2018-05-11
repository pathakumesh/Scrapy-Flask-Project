# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem
import json
from urllib import urlencode,quote, pathname2url
from scrapy.http import HtmlResponse




class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["gottman.com","disqus.com"]
    start_urls = ['https://www.gottman.com/blog/category/archives/']
    

    def parse(self, response):
        print 'next_page_url ', response.url
        blog_posts = response.xpath('//article[@class= "article-tile "]')
        
        for sub_blog in  blog_posts:
            item = BlogExtractItem()


            #Get Title, Link, Date
            title = sub_blog.xpath('h3/a/text()').extract_first()
            if not title:
                title = sub_blog.xpath('h3/a/strong/text()').extract_first()
            title = title.strip()
            link = sub_blog.xpath('h3/a/@href').extract_first()
            
                
            item['title'] = replace_special_chars(title)
            item['link'] = link
            
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request
        
        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(), "Older posts")]')
        if next_page:
            next_page_url = self.start_urls[0] +  next_page.xpath('@href').extract_first().split('archives/')[1]
            yield scrapy.Request(next_page_url, callback=self.parse)
        
    def parse_sub_blog(self, response):
        item = response.meta['item']
        
        author = response.xpath('//span[@class="byline author vcard"]/a/text()').extract_first()
        if not author:
            author = response.xpath('//span[@class="byline author vcard"]/text()').extract_first()
            if author:
                author = author.strip()
        date = response.xpath('//time[@itemprop= "datePublished"]/text()').extract_first()
        item['author'] = author
        item['date'] = date
        
        post_id = response.xpath('//article[contains(@class, "type-post status-publish")]/@class').re(r'post-(\d+)\s*')[0]
        word_count = 0

        # Find the actual article block
        main_block = response.xpath('//div[@class="entry-content"]/*')
        end_tag = ["gf_browser_chrome gform_wrapper"]
        word_count = 0
        for block in main_block:
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in end_tag:
                break
            block_string = block.xpath('string()').extract()[0]            
            word_count += get_word_count(block_string)
        
        item['word_count'] = word_count
        
        comments_url = get_comments_url(item['link'], item['title'], post_id)
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
            .replace('\xe2\x80\x94', '\--').replace('\xe2\x80\xa6', '...')\
            .replace('#', '%23')
    params =  {
        "base": "default",
        "f": "gottmaninstitute",
        "t_u": link,
        "t_i": "%s https://gottman.com/?p=%s" % (post_id, post_id),
        "t_e": title,
        "t_d": title,
        "t_t": title,
        "s_o": "default"
    }
    try:
        comments_url = "https://disqus.com/embed/comments/?" + '&'.join("%s=%s" % (k,v) for k,v in params.iteritems()) +"#version=90b177d97dda66d90b9275eb687a8640"
    except:
        print "EXCEPTION for link: "
        print link
        print title
        print post_id
        return "https://disqus.com/embed/comments/?"
    return comments_url




            