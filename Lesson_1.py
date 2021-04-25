import json
import time
from pathlib import Path
import requests


class Parse5ka:
    headers = {
        "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
    }
    params = {
        "records_per_page": 20,
    }

    def __init__(self, star_url: str, save_path: Path, cat, cat_url):
        self.star_url = star_url
        self.save_path = save_path
        self.cat = cat
        self.cat_url = cat_url

    @staticmethod
    def get_response(url, *args, **kwargs):
        while True:
            response = requests.get(url, *args, **kwargs)
            if response.status_code == 200:
                return response
            time.sleep(3)

    def run(self):
        file_path = self.save_path.joinpath(f"{self.cat['parent_group_name']}.json")
        self.write_template(file_path)
        for product in self._parse(self.star_url):
            self._save(product, file_path)

    def _parse(self, url: str):
        while url:
            time.sleep(0.1)
            self.params = {
                "records_per_page": 20,
                "categories": self.cat['parent_group_code']
            }
            response = self.get_response(url, headers=self.headers, params=self.params)
            data = response.json()
            if data['next']:
                data['next'] = data['next'].replace('monolith', '5ka.ru')
            url = data["next"]
            for product in data["results"]:
                yield product

    def write_template(self, file):
        template = {
            'category name': self.cat['parent_group_name'],
            'category code': self.cat['parent_group_name'],
            'products': [],
        }
        with open(file, 'w') as f:
            f.write(json.dumps(template, ensure_ascii=False))

    def _save(self, data: dict, file_path):
        with open(file_path, 'r+') as f:
            content = json.load(f)
            content['products'].append(data)
            file_path.write_text(json.dumps(content, ensure_ascii=False))

    def get_cat(self):
        for category in self.get_response(url=self.cat_url, headers=self.headers, params=self.params).json():
            yield category


def get_save_path(dir_name):
    save_path = Path(__file__).parent.joinpath(dir_name)
    if not save_path.exists():
        save_path.mkdir()
    return save_path


if __name__ == "__main__":
    save_path = get_save_path("products")
    cat_url = "https://5ka.ru/api/v2/categories/"
    shop_url = 'https://5ka.ru/api/v2/special_offers/'
    cat_parser = Parse5ka(shop_url, save_path, cat=None, cat_url=cat_url, )
    for i in cat_parser.get_cat():
        cat_parser.cat = i
        cat_parser.run()
