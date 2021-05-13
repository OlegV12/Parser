import re
from urllib.parse import urljoin

from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose


def join_array(items):
    return "".join(items)


def join_user_url(user_id):
    return urljoin("https://hh.ru/", user_id)


def join_seller_url(seller_url):
    ulrs = []
    for i in seller_url:
        ulrs.append(urljoin("https://avito.ru/", i))
    return ulrs


def strip_addr(addr):
    plain_addr = addr.replace("\n", "")
    plain_addr = plain_addr.strip()
    return plain_addr


def strip_params(params):
    strip_params = [i for i in params if i != " " and i != "\n " and i != "\n  "]
    params_dict = {strip_params[itm].replace(":", ""): strip_params[itm+1].strip() for itm in range(0, len(strip_params), 2)}
    return params_dict

class HHLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_out = TakeFirst()
    salary_in = join_array
    description_in = join_array
    author_in = MapCompose(join_user_url)
    author_out = TakeFirst()


class AvitoLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_out = TakeFirst()
    price_out = TakeFirst()
    address_in = MapCompose(strip_addr)
    address_out = TakeFirst()
    seller_url_out = join_seller_url
    parameters_out = strip_params
