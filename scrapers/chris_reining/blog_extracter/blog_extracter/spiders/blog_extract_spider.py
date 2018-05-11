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
    allowed_domains = ["chrisreining.com","disqus.com"]
    start_urls = ['https://chrisreining.com/articles/']
    intermediate_url = "https://chrisreining.com/wp-admin/admin-ajax.php"
    page_number = 1

    def parse(self, response):
        if not self.page_number == 1:
            data =  json.loads(response.text)
            body = data['data']
            response = HtmlResponse(url=response.url, body=body, encoding='utf-8')
        blog_posts = response.xpath('//article[contains(@class, "post-")]')
        
        if not blog_posts:
            return

        for sub_blog in  blog_posts:
            item = BlogExtractItem()

            post_id = sub_blog.xpath('@class')[0].re(r'post-(\d+)')[0]

            #Get Title, Link, Date
            title = sub_blog.xpath('div/header/h2[@class="entry-title"]/a/text()').extract_first()
            if not title:
                title = sub_blog.xpath('div/header/h2[@class="entry-title"]/a/strong/text()').extract_first()
            title = title.strip()
            link = sub_blog.xpath('div/header/h2[@class="entry-title"]/a/@href').extract_first()
            
                
            item['title'] = replace_special_chars(title)
            item['link'] = link
            
            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            request.meta['post_id'] = post_id
            yield request
        
        self.page_number += 1
        yield scrapy.FormRequest(
            url= self.intermediate_url,
            formdata={"action": "be_ajax_load_more",
                    "nonce": "5622db3955",
                    "page": str(self.page_number),
                    "query[pagename]": "articles"
            },
            callback=self.parse,
            dont_filter = True
        )
        
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0

        # Find the actual article block
        main_block = response.xpath('//div[@class="blog-archive-lower-wrap"]/*')
        
        word_count = 0
        for block in main_block:
            
            block_string = block.xpath('string()').extract()[0]
            if u"If you’d like to get my help personally you can" in block_string:
                continue
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
            .replace('\xe2\x80\x94', '\--').replace('\xe2\x80\xa6', '...')\
            .replace('#', '%23')
    params =  {
        "base": "default",
        "f": "mreverydaydollar",
        "t_u": link,
        "t_i": "%s https://chrisreining.com/?p=%s" % (post_id, post_id),
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




            