# -*- coding: utf-8 -*-

import re
import scrapy
import logging as log
from blog_extracter.items import BlogExtractItem


class BlogExtractSpider(scrapy.Spider):
    name = "blog_extract_spider"
    allowed_domains = ["thecollegeinvestor.com"]
    start_urls = ['https://thecollegeinvestor.com/']

    def parse(self, response):
        print 'next_page_url ', response.url
        blogs = response.xpath('//a[@class="entry-title-link"]')
        for sub_blog in blogs:
            item = BlogExtractItem()

            #Get Title, Link
            title = sub_blog.xpath('text()').extract_first()
            link = sub_blog.xpath('@href').extract_first()
            
            
            item['title'] = replace_special_chars(title)
            item['link'] = link

            # Make a request to actual link for the blog to extract other info
            request =  scrapy.Request(item['link'], callback=self.parse_sub_blog)
            request.meta['item'] = item
            yield request

        # If next page is there, make a request and proceed similar as above.
        next_page = response.xpath('//a[contains(text(),"Next Page")]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            yield scrapy.Request(next_page_url, callback=self.parse)
        
            
    def parse_sub_blog(self, response):
        item = response.meta['item']
        date =  response.xpath('//meta[@property="article:published_time"]/@content').re(r'(.*?)T')
        if date:
            item['date'] = date[0]
        item['author'] = response.xpath('//span[@class="entry-author-name"]/text()').extract_first()
        comments_count = response.xpath('//span[@class="entry-comments-link"]/a').re(r'(\d+)\s*Comment')
        item['comments_count'] = comments_count[0] if comments_count else 0
        
        main_block = response.xpath('//div[@class="entry-content"]//div[contains(@class, "thrv_wrapper thrv_text_element") or contains(@class, "thrv_wrapper thrv-styled_list")]/*')
        children = True
        if not main_block:
            main_block = response.xpath('//div[@class="entry-content"]/*')
            children = False
        ignore_tags = ["tve_leads_end_content", "tve-leads-post-footer tve-tl-anim tve-leads-track-post_footer-22 tl-anim-instant tve-leads-triggered"]
        continue_tags = ["nc_socialPanel swp_flatFresh swp_d_fullColor swp_i_fullColor swp_o_fullColor scale-120 scale-fullWidth swp_one",
                        "thrv_wrapper thrv_custom_html_shortcode", "thrv_wrapper thrv_contents_table",
                        "thrv_wrapper thrv-button", "thrv_wrapper tve_wp_shortcode on_hover", "thrv_wrapper thrv_button_shortcode tve_centerBtn"]
        word_count = 0
        for block in main_block:
            if block.xpath('@id').extract_first() and block.xpath("@id").extract_first() in ignore_tags:
                break
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in ignore_tags:
                break
            if block.xpath('@class').extract_first() and block.xpath("@class").extract_first() in continue_tags:
                continue
            if bool(block.xpath('./@data-css')):
                continue
            if bool(block.xpath('../../@data-css')):
                continue
            block_string =  block.xpath('string()').extract()[0]    
            word_count += get_word_count(block_string)
        if children and word_count<1500:
            word_count += 20
        elif children and word_count>1500:
            word_count += 40
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
            _line = re.sub(r'<img.*>', '', _line)
            _line = re.sub(u'\u25cf\t', '', _line)
            _line = re.sub(u'\u2013', '-', _line)
            _line = re.sub(u'\u2014', '- ', _line)
            _line = re.sub(r'([a-z])(\.|\?)([A-Z])', r'\1\2 \3', _line)

            
            _line = _line.replace(u'\xe2\x80\x9d', '')
            _line = _line.replace(u'\xe2\x80\x9c', '')
            _line = _line.replace(u'\u2026', ' ')
            _line = _line.replace('- ', ' ')
            # _line = _line.replace('.', '')
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