# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["lovesagame.com"]
    start_urls = ['https://lovesagame.com']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//div[@class="inside-article"]')
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link
            title = sub_blog.xpath('header/h2/a/text()').extract_first()
            link = sub_blog.xpath('header/h2/a/@href').extract_first()
            comments_count = sub_blog.xpath('footer/span[@class="comments-link"]/a').re(r'(\d+)\s*Comment')
            
            item['title'] = replace_special_chars(title)
            item['link'] = link
            item['comments_count'] = comments_count[0] if comments_count else None

            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request

        # If next page is there, make a request and proceed similar as above.
        # next_page = response.xpath('//a[@class="next page-numbers"]')
        next_page =  response.xpath('//a[@class="next page-numbers"]')
        # next_page = response.xpath('//a[contains(text(), "Next")]')

        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            request =  scrapy.Request(next_page_url, callback=self.parse)
            request.meta['dont_redirect'] = True
            request.meta['handle_httpstatus_all'] = True
            yield request
        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']

        author = response.xpath('//a[@class="author-name"]/span/text()').extract_first()
        item['author'] = author
        
        date =  response.xpath('//meta[@property="article:published_time"]/@content').re(r'(.*?)T')
        if date:
            item['date'] = date[0]
        
        main_block = response.xpath('//div[@class="tve-tl-cnt-wrap"]/*')
        if not main_block:
            main_block = response.xpath('//div[@class="entry-content"]/*')

        ignore_tags = ["tve_leads_end_content"]
        continue_tags = ["nc_socialPanel swp_flatFresh swp_d_dgOutlines swp_i_fullColor swp_o_fullColor scale-100 scale-fullWidth swp_one",
                        "mejs-container mejs-container-keyboard-inactive wp-audio-shortcode mejs-audio",
                        "tve-leads-in-content tve-tl-anim tve-leads-track-in_content-1 tl-anim-instant tve-leads-triggered"]
        ignore_strings = ["sw-pinit aligncenter size-full wp-image-", "mejs-offscreen", "sw-pinit aligncenter size-full wp-image-6428"]
        word_count = 0
        for block in main_block[1:]:
            if block.xpath('@id').extract_first() and block.xpath("@id").extract_first() in ignore_tags:
                break
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in continue_tags:
                continue
            if any(s in block.extract() for s in ignore_strings):
                continue
    
            block_string =  block.xpath('string()').extract()[0]
            word_count += get_word_count(block_string)
        item['word_count'] = word_count - 35
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