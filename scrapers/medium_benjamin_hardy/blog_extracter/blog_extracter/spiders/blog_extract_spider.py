# -*- coding: utf-8 -*-

import re
import json
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["medium.com"]
    quotes_base_url = "https://medium.com/_/api/users/5153880ce2ee/profile/stream?limit=8&to=%s&source=overview&page=%s"
    start_urls = [quotes_base_url % (1522078067611,1)]

    def parse(self, response):
        data = json.loads(response.body.replace("])}while(1);</x>", ''))
        

        posts = data.get('payload',{}).get('references',{}).get('Post',{})
        for post in posts.values():

            item = BlogExtractItem()
            item['title'] = post['title']
            item['link'] = "https://medium.com/@benjaminhardy/" + post['uniqueSlug']
            # print item['title'], blog_url
            request = scrapy.Request(item['link'], self.parse_sub_blog)
            request.meta['item'] = item
            yield request

        _next_page = data.get('payload',{}).get('paging',{}).get('next')
        if _next_page:
            _to = _next_page['to']
            _page_num = _next_page['page']
            yield scrapy.Request(self.quotes_base_url % (_to, _page_num))
        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0
        header = response.xpath('//div[@class= "u-flex1 u-paddingLeft15 u-overflowHidden"]')
        
        # Don't proceed for other users
        if not header.xpath('//a[@data-user-id="5153880ce2ee"]'):
            return

        item['author'] = header.xpath('//a[@data-user-id="5153880ce2ee"]/text()').extract()[0]
        item['date'] = header.xpath('div[@class = "ui-caption postMetaInline js-testPostMetaInlineSupplemental"]/time[@datetime]')\
                        .re(r'(\d+-\d+-\d+)')[0]

        # Find the actual article block
        article = response.xpath('//div[@class= "section-inner sectionLayout--insetColumn"]/*')
    
        for sub_block in article[1:]:            
            #Extract the plain text and count the words
            block_line = sub_block.xpath('string()').extract()[0]
            word_count += get_word_count(block_line)

        item['word_count'] = word_count

        #Get the total number of comments if available
        comments_count = response.xpath('//div[@class="buttonSet u-flex0"]/\
                    button[@class="button button--chromeless u-baseColor--buttonNormal"]/text()').extract_first()
        item['comments_count'] = comments_count
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
    



            