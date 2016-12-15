# -*- coding: utf-8 -*-
import json

from w3lib.util import str_to_unicode

from scrapely.htmlpage import HtmlPage, page_to_dict, url_to_page, xml_to_page
from scrapely.template import TemplateMaker, best_match
from scrapely.extraction import InstanceBasedLearningExtractor


class Scraper(object):

    def __init__(self, templates=None):
        """Initialize an empty scraper."""
        self._templates = templates or []
        self._ex = None

    @classmethod
    def fromfile(cls, file):
        """Initialize a scraper from a file previously stored by tofile()
        method.
        """
        templates = [HtmlPage(**x) for x in json.load(file)['templates']]
        return cls(templates)

    def tofile(self, file):
        """Store the scraper into the given file-like object"""
        tpls = [page_to_dict(x) for x in self._templates]
        json.dump({'templates': tpls}, file)

    def add_template(self, template):
        self._templates.append(template)
        self._ex = None

    def train_from_htmlpage(self, htmlpage, data, weights=None, required=None, allow_html=None):
        assert data, "Cannot train with empty data"
        tm = TemplateMaker(htmlpage)
        for field, values in data.items():
            if (isinstance(values, (bytes, str)) or
                    not hasattr(values, '__iter__')):
                values = [values]
            for value in values:
                value = str_to_unicode(value, htmlpage.encoding)
                # Checking if the field in weights dict to take the value.
                weight = weights[field] if weights and field in weights else 1.0
                # Checking if the field in allow_html dict to take the value.
                is_allow_html = allow_html[field] if allow_html and field in allow_html else True
                # Checking if the field in required list to take the value.
                is_required = required[field] if required and field in required else False
                tm.annotate(field, best_match(value), weight=weight, is_required=is_required,
                            is_allow_html=is_allow_html)
        self.add_template(tm.get_template())

    def train(self, url, data, xml=None, encoding=None, weights=None, required=None, allow_html=None):
        if xml:
            page = xml_to_page(url, xml, encoding='utf-8')
        else:
            page = url_to_page(url, encoding)
        self.train_from_htmlpage(page, data, weights, required, allow_html)

    def scrape(self, url, xml=None, encoding=None):
        if xml:
            page = xml_to_page(url, xml, encoding='utf-8')
        else:
            page = url_to_page(url, encoding)
        return self.scrape_page(page)

    def scrape_page(self, page):
        if self._ex is None:
            self._ex = InstanceBasedLearningExtractor((t, None) for t in
                    self._templates)
        return self._ex.extract(page)[0]
