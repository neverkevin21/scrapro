#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import fire

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scrapro.spiders import ScraproSpider

prj_dir = os.path.dirname(os.path.realpath(__file__))
tmpl_dir = os.path.join(prj_dir, 'tmpls')


def process(tmpl):
    tmpl_path = os.path.join(tmpl_dir, '{}.yaml'.format(tmpl))
    # TODO: Tmpl Obj.
    with open(tmpl_path, 'r') as f:
        conf = yaml.load(f)
    custom_settings = conf['settings']
    # TODO: configure settings for each spider.
    settings = get_project_settings()
    for k, v in custom_settings.items():
        if k in settings.keys():
            if isinstance(v, dict):
                settings.update({k: v})
            elif isinstance(v, list):
                settings.get(k).append(v)
            else:
                settings.set(k, v)
        else:
            settings.set(k, v)
    process = CrawlerProcess(settings)
    process.crawl(ScraproSpider, tmpl_path)
    process.start()


if __name__ == "__main__":
    fire.Fire(process)
