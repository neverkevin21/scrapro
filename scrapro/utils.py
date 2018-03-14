# -*- coding: utf-8 -*-


from scrapy.utils.project import get_project_settings


def configure_settings(custom_settings):
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
    return settings
