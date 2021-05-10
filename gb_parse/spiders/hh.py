import scrapy
import re
import pymongo
from ..loaders import HHLoader


class HhSpider(scrapy.Spider):
    name = "headhunter"
    allowed_domains = ["hh.ru"]
    start_urls = ["https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113"]

    xpath_selectors = {
        "pages": '//a[@data-qa="pager-next"]/@href',
        "vacancy": '//a[@data-qa="vacancy-serp__vacancy-title"]/@href',
        "employer": '//a[@data-qa="vacancy-company-name"]/@href'
    }

    xpath_vacancy_selectors = {
        "title": '//h1[@data-qa="vacancy-title"]/text()',
        "salary": '//p[@class="vacancy-salary"]/span/text()',
        "description": '//div[@data-qa="vacancy-description"]//text()',
        "tags": '//div[@data-qa="bloko-tag bloko-tag_inline skills-element"]//text()',
        "employer": '//a[@data-qa="vacancy-company-name"]/@href',
    }

    xpath_employer_selectors = {
        "title": "//div[@class='company-header']//h1//text()",
        "website": "//a[@data-qa='sidebar-company-site']/@href",
        "areas_of_activity": "//div[@class='employer-sidebar-block']/p/text()",
        "vacancies": "//a[@data-qa='vacancy-serp__vacancy-title']/@href",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_client = pymongo.MongoClient()

    def _get_follow(self, response, selector_str, callback):
        for itm in response.xpath(selector_str):
            yield response.follow(itm, callback=callback)

    def parse(self, response, *args, **kwargs):
        yield from self._get_follow(
            response, self.xpath_selectors["pages"], self.parse
        )
        yield from self._get_follow(
            response,
            self.xpath_selectors["vacancy"],
            self.vacancy_parse,
        )

    def vacancy_parse(self, response):
        loader = HHLoader(response=response)
        loader.add_value("url", response.url)
        for key, xpath in self.xpath_vacancy_selectors.items():
            loader.add_xpath(key, xpath)

        yield loader.load_item()

        yield from self._get_follow(
            response,
            self.xpath_vacancy_selectors["employer"],
            self.author_parse,
        )

    def author_parse(self, response):
        loader = HHLoader(response=response)
        employer = {"url": response.url}
        loader.add_value("employer", employer)
        for key, xpath in self.xpath_employer_selectors.items():
            loader.add_xpath(key, xpath)

        yield loader.load_item()
