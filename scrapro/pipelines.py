# -*- coding: utf-8 -*-


from pprint import pprint

class TestPipeline(object):
    def process_item(self, item, spider):
        print 'scraped item: '
        pprint(item)
        return item
