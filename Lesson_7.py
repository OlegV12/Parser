from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gb_parse.spiders.instagram import InstagramSpider
import os
import dotenv

if __name__ == "__main__":
    dotenv.load_dotenv('.env')
    crawler_settings = Settings()
    crawler_settings.setmodule("gb_parse.settings")
    crawler_process = CrawlerProcess(settings=crawler_settings)
    tags = ["python"]
    crawler_process.crawl(InstagramSpider,
                          login=os.getenv("INST_LOGIN"),
                          password=os.getenv("INST_PASS"),
                          tags=tags,
                          )
    crawler_process.start()
