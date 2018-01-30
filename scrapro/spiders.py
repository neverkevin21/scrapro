# -*- coding: utf-8 -*-

import re
import six
import json
import yaml
import copy
import types
import scrapy

from scrapy import Request
from scrapy.item import DictItem
from scrapy.http import Response
from scrapy.exceptions import NotConfigured

_tmpl = """
def %(func)s(self, response):
    conf = self.tmpl['steps']['%(func)s']
    items = conf.get('items')
    _cyield = conf.get('yield')
    return self._extract_item(items, _cyield, response)

_func = %(func)s
"""


class ScraproSpider(scrapy.Spider):
    name = 'scrapro'

    def __init__(self, tmpl_path):
        with open(tmpl_path, 'r') as f:
            self.tmpl = yaml.load(f)
        self.__prepare__()
        super(ScraproSpider, self).__init__()

    def __prepare__(self):
        steps = self.tmpl['steps']
        for step in steps.keys():
            exec _tmpl % {'func': step}
            self.__dict__[step] = types.MethodType(_func, self, None)

    def start_requests(self):
        conf = self.tmpl['start_requests']
        urls_key = self._find_key(conf, 'urls')
        if not urls_key:
            raise NotConfigured
        urls = self._extract(urls_key, conf[urls_key], None)
        for url in urls:
            yield Request(url, self.parse)

    def _extract_item(self, items, _cyield, response):
        meta = response.meta
        meta_data = meta.get('data', {})
        line_key = self._find_key(items, 'line')
        if line_key:
            v = items[line_key]
            lines = self._extract(line_key, v, response)
            items.pop(line_key)
            for line in lines:
                data = {k.rsplit('_')[0]: self._extract(k, v, response, line=line)
                        for k, v in items.items() if k != 'yield'}
                data.update(meta_data)
                yield self._yield(items, response, data)
        else:
            data = {k.rsplit('_')[0]: self._extract(k, v, response)
                    for k, v in items.items() if k != 'yield'}
            data.update(meta_data)
        if _cyield:
            yield self._yield({'yield': _cyield}, response, data)

    def _yield(self, items, response, data):
        if not items.get('yield'):
            return None
        info = items.get('yield')
        if isinstance(info, six.string_types):
            if info != 'item':
                raise TypeError("unkwnown yield type, excepting `item`.")
            item_cls = self.create_item('ScraproItem', data.keys())
            item = item_cls(data)
            return item

        elif isinstance(info, dict):
            info = copy.deepcopy(info)
            url_key = self._find_key(info, 'url')
            if not url_key:
                raise NotConfigured("need param url.")
            v = info.pop(url_key)
            url = self._extract(url_key, v, response, data=data)
            callback = info.pop('callback')
            kwargs = self._parse_yield(info, data)
            return Request(url, getattr(self, callback), **kwargs)
        else:
            raise TypeError("Unexcepted yield type, excepting string or dict.")

    def create_item(self, cls, field_list):
        fields = {name: scrapy.Field() for name in field_list}
        return type(cls, (DictItem,), {'fields': fields})

    def _parse_yield(self, info, data):
        if 'meta' in info:
            for k, v in info['meta'].items():
                if '_' not in k:
                    continue
                info['meta'][k.rsplit('_')[0]] = self._extract(k, v, None, data=data)
                info['meta'].pop(k)
        return info

    def _extract(self, k, v, response, **kwargs):
        response = kwargs.get('line', response)
        data = kwargs.get('data')

        if '_' not in k:
            return v

        k, ktype = k.rsplit('_')
        if isinstance(v, six.string_types):
            exps, arr = v, False
        elif isinstance(v, dict):
            exps, arr = v['val'], v['arr']
        else:
            raise TypeError("Unexcepted Item type, excepting string or dict")

        if ktype in ('xpath', 'css'):
            if k == 'lines':
                return response.xpath(exps)
            return response.xpath(exps).extract() if arr else response.xpath(exps).extract_first()

        if ktype == 're':
            result = re.findall(exps, response)
            return result if arr else result[0]

        if ktype == 'code':
            exec exps
            return val

        if ktype == 'eval':
            return eval(exps)

        if ktype == 'json':
            if isinstance(response, Response):
                response = json.loads(response.body)
            elif isinstance(response, six.string_types):
                response = json.loads(response)
            keys = exps.split('.')
            tmp = response
            for key in keys:
                tmp = tmp[key]
            return tmp

    def _find_key(self, d, prefix):
        _key = [k for k in d.keys() if k.startswith(prefix)]
        if _key:
            return _key[0]
        return None
