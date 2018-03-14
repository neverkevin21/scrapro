#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import fire

from scrapy.crawler import CrawlerProcess

from scrapro.utils import configure_settings
from scrapro.spiders import ScraproSpider

prj_dir = os.path.dirname(os.path.realpath(__file__))
tmpl_dir = os.path.join(prj_dir, 'tmpls')


def run(tmpl):
    tmpl_path = os.path.join(tmpl_dir, '{}.yaml'.format(tmpl))
    # TODO: Tmpl Obj.
    with open(tmpl_path, 'r') as f:
        conf = yaml.load(f)
    custom_settings = conf['settings']
    # TODO: configure settings for each spider.
    settings = configure_settings(custom_settings)
    process = CrawlerProcess(settings)
    process.crawl(ScraproSpider, tmpl_path)
    process.start()


if __name__ == "__main__":
    fire.Fire(run)
