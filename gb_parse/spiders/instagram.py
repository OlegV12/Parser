import scrapy
import json
from ..loaders import TagLoader, PostLoader
import datetime
import copy


class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["www.instagram.com", "i.instagram.com"]
    start_urls = ["https://www.instagram.com/accounts/login/"]
    _login_url = "https://www.instagram.com/accounts/login/ajax/"
    _tags_path = "/explore/tags/"
    _pagination_url = "/api/v1/tags/"

    def __init__(self, login, password, tags, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login = login
        self.password = password
        self.tags = tags

    def parse(self, response, **kwargs):
        try:
            js_data = self.js_data_extract(response)

            yield scrapy.FormRequest(
                self._login_url,
                method="POST",
                callback=self.parse,
                formdata={"username": self.login, "enc_password": self.password},
                headers={"X-CSRFToken": js_data["config"]["csrf_token"]},
            )
        except AttributeError:
            if response.json()["authenticated"]:
                for tag in self.tags:
                    yield response.follow(f"{self._tags_path}{tag}/", callback=self.tag_page_parse)

    def tag_page_parse(self, response):
        data = self.js_data_extract(response)
        tag_data = copy.deepcopy(data['entry_data']['TagPage'][0]['data'])
        del tag_data['top']
        del tag_data['recent']
        tag_loader = TagLoader(tag_data=tag_data)
        tag_loader.add_value("date_parse", datetime.datetime.now())
        tag_loader.add_value("data", data['entry_data']['TagPage'][0]['data'])
        yield tag_loader.load_item()

        recent = data['entry_data']['TagPage'][0]['data'].pop('recent')
        yield from self.post_page_parse(recent)

    def post_page_parse(self, data):
        sections = data.pop('sections')
        for section in sections:
            for media in section['layout_content']['medias']:
                post_loader = PostLoader(media=media)
                post_loader.add_value("date_parse", datetime.datetime.now())
                post_loader.add_value("data", media)
                yield post_loader.load_item()

    def js_data_extract(self, response):
        script = response.xpath(
            "//script[contains(text(), 'window._sharedData =')]/text()"
        ).extract_first()
        return json.loads(script.replace("window._sharedData = ", "")[:-1])
