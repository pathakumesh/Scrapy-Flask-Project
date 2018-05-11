# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["lovein90days.com"]
    start_urls = ['http://lovein90days.com/relationship-advice-blog/']

    def parse(self, response):
        content = response.xpath('//main[@class="content"]')
        for sub_blog in  content.xpath('article/header/h2[@class="entry-title"]/a'):
            item = BlogExtractItem()
            
            #Get Title, Link, Date
            title = sub_blog.xpath('text()').extract_first()
            link = sub_blog.xpath('@href').extract_first()
            
            item['title'] = replace_special_chars(title)
            item['link'] = link

            #Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(link, callback=self.parse_sub_blog)
            request.meta['item'] = item
            
            yield request
        
        #If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(), "Next Page")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        word_count = 0

        # Find the actual article block
        article =  response.xpath('//article[@itemtype= "https://schema.org/CreativeWork"]')

        #extract date from the time tag
        date = article.xpath('//time[@itemprop="datePublished"]/text()').extract()[0]
        item['date'] = date
        
        #all the content are in div and p tags, find them
        divs = article.xpath('header[@class="entry-header"]/following-sibling::div')
        ps = article.xpath('header[@class="entry-header"]/following-sibling::p')
        
        for div in divs:

            #exclude unnecessary divs
            if div.xpath('div[@class = "dd_buttons"]') or div.xpath('div[@class = "wp-biographia-text-no-pic"]'):
                continue
            
            #Extract the plain text and count the words
            div_line = div.xpath('string()').extract()[0]
            word_count += get_word_count(div_line)

        for p in ps:
            #Extract the plain text and count the words
            p_line = p.xpath('string()').extract()[0]
            word_count += get_word_count(p_line)

        
        item['word_count'] = word_count

        # Get the author name
        about_block = response.xpath('//div[@class="wp-biographia-text-no-pic"]/h3')
        author = about_block.xpath('text()').re(r'.*About (.*)')[0] if about_block else 'N/A'
        item['author'] = author

        #Get the total number of comments if available
        comments = response.xpath('//div[@class="entry-comments"]')
        comments_count = len(comments.xpath('ol[@class="comment-list"]/li')) if comments else 0
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
    



            