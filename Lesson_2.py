import time
import typing

import requests
from urllib.parse import urljoin
from pymongo import MongoClient
import bs4


class GbBlogParse:
    def __init__(self, start_url, collection):
        self.time = time.time()
        self.start_url = start_url
        self.collection = collection
        self.done_urls = set()
        self.tasks = []
        start_task = self.get_task(self.start_url, self.parse_feed)
        self.tasks.append(start_task)
        self.done_urls.add(self.start_url)

    def _get_response(self, url, *args, **kwargs):
        if self.time + 0.9 < time.time():
            time.sleep(0.5)
        response = requests.get(url, *args, **kwargs)
        self.time = time.time()
        print(url)
        return response

    def _get_soup(self, url, *args, **kwargs):
        soup = bs4.BeautifulSoup(self._get_response(url, *args, **kwargs).text, "lxml")
        return soup

    def get_task(self, url: str, callback: typing.Callable) -> typing.Callable:
        def task():
            soup = self._get_soup(url)
            return callback(url, soup)

        if url in self.done_urls:
            return lambda *_, **__: None
        self.done_urls.add(url)
        return task

    def task_creator(self, links, callback):

        for link in links:
            task = self.get_task(link, callback)
            self.tasks.append(task)

    def parse_feed(self, url, soup):
        ul_pagination = soup.find("ul", attrs={"class": "gb__pagination"})
        links = set(urljoin(url, itm.attrs.get('href')) for itm in ul_pagination.find_all('a') if itm.attrs.get('href'))
        self.task_creator(links, self.parse_feed)
        post_wrapper = soup.find("div", attrs={"class": "post-items-wrapper"})
        links = set(urljoin(url, itm.attrs.get("href")) for itm in
                    post_wrapper.find_all('a', attrs={'class': 'post-item__title'}) if itm.attrs.get('href'))
        self.task_creator(
            links, self.parse_post
        )

    def get_comment(self, comment_data):
        comment_list = []
        if comment_data:
            for i in comment_data:
                comment_dict = dict()
                comment_dict[i['comment']['user']['full_name']] = i['comment']['body']
                comment_dict[f'response to {i["comment"]["user"]["full_name"]}'] = \
                    self.get_comment(i['comment']['children'])
                comment_list.append(comment_dict)

            return comment_list

    def parse_post(self, url, soup):
        title_tag = soup.find("h1", attrs={"class": "blogpost-title"})
        blog_content = soup.find("div", attrs={"class": "blogpost-content"})
        img = str(blog_content.find("img")['src'])
        date = soup.find("div", attrs={"class": "blogpost-date-views"})
        date_time = date.find("time")['datetime']
        author = soup.find("div", attrs={"itemprop": "author"})
        post_id = soup.find("comments").attrs.get("commentable-id")
        comment_api = f"/api/v2/comments?commentable_type=Post&commentable_id={post_id}&order=desc"
        comment_data = self._get_response(urljoin(self.start_url, comment_api)).json()

        data = {
            "url": url,
            "title": title_tag.text,
            "img": img,
            "post_datetime": date_time,
            "author": author.text,
            "author_url": urljoin(url, author.parent.attrs.get("href")),

            "comment": self.get_comment(comment_data)}
        return data

    def run(self):
        for task in self.tasks:
            task_result = task()
            if isinstance(task_result, dict):
                self.save(task_result)

    def save(self, data):
        self.collection.insert_one(data)


if __name__ == "__main__":
    collection = MongoClient()["gb_parse_20_04"]["gb_blog"]
    parser = GbBlogParse("https://gb.ru/posts", collection)
    parser.run()
