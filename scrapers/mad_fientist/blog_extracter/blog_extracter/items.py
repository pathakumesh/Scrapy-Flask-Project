# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BlogExtractItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    link = scrapy.Field()
    word_count = scrapy.Field()
    date = scrapy.Field()
    author = scrapy.Field()
    comments_count = scrapy.Field()
    notes = scrapy.Field()
    pass
