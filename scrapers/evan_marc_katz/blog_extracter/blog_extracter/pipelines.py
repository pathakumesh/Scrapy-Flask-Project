# -*- coding: utf-8 -*-
import os
import time
import csv
from scrapy import signals
from scrapy.exporters import CsvItemExporter
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class BlogExtractPipeline(object):
    def __init__(self):
        self.files = {}
        self.file_name = 'scraped_output.csv'
        self.export_fields = ['title','link','word_count','date','author','comments_count','notes']
        self.notes_map = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        #Check if previously scraped out is there or not. If yes, extract the notes from previous file
        self.notes_map = self.find_old_notes_map()
        
        output_file = open(self.file_name, 'w+b')
        self.files[spider] = output_file
        self.exporter = CsvItemExporter(output_file,fields_to_export = self.export_fields)
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        output_file = self.files.pop(spider)
        output_file.close()
        self.post_process_after_spider_close()
    
    def post_process_after_spider_close(self):
        for fname in os.listdir('.'):
            if fname.endswith('.last_scraped'):
                os.remove(fname)
            if fname == 'running':
                os.remove(fname)

        timestr = time.strftime("%Y-%m-%d-%H:%M:%S")
        open('%s.last_scraped' % timestr,'w').close()

    def process_item(self, item, spider):
        #Update notes from the previously scraped file
        item['notes'] = self.notes_map.get(item['link'], '')
        
        self.exporter.export_item(item)
        return item

    def find_old_notes_map(self):
        notes_map = {}
        dir_path = os.path.dirname(os.path.realpath(__file__))
        full_file_path = '%s/%s' % (dir_path.rsplit('/',1)[0], self.file_name)
        if os.path.exists(full_file_path):
            with open(full_file_path, "r") as myfile:
                file_= csv.reader(myfile, delimiter=',')
                for row in file_:
                    if row[6] != '' and row[6] != 'link':
                        notes_map.update({row[1]: row[6]})
        return notes_map