import scrapy
import pymongo
from ..loaders import AvitoLoader


class AvitoSpider(scrapy.Spider):
    name = "avito"
    allowed_domains = ["avito.ru"]
    start_urls = ["https://www.avito.ru/moskva/kvartiry/prodam"]

    _xpath_selectors = {
        "pagination": '//a[@class="pagination-page"]/@href',
        "flat_url": '//a[@data-marker="item-title"]/@href',
    }

    _xpath_data_selectors = {
        "title": '//h1[@class="title-info-title"]/span[@class="title-info-title-text"]/text()',
        "price": '//div[@class="item-price-wrapper"]/div[@id="price-value"]//span[@itemprop="price"]/text()',
        "address": '//div[@itemprop="address"]/span[@class="item-address__string"]/text()',
        "parameters": '//div[@class="item-params"]//li[@class="item-params-list-item"]//text()',
        "seller_url": '//div[@data-marker="seller-info/name"]/a/@href'
    }



    def _get_follow(self, response, selector_str, callback):
        for itm in response.xpath(selector_str):
            yield response.follow(itm, callback=callback)

    def parse(self, response, *args, **kwargs):
        yield from self._get_follow(
            response, self._xpath_selectors["pagination"], self.parse
        )
        yield from self._get_follow(
            response,
            self._xpath_selectors["flat_url"],
            self.flat_parse,
        )

    def flat_parse(self, response):
        flat_loader = AvitoLoader(response=response)
        flat_loader.add_value("url", response.url)
        for key, xpath in self._xpath_data_selectors.items():
            flat_loader.add_xpath(key, xpath)
        yield flat_loader.load_item()
