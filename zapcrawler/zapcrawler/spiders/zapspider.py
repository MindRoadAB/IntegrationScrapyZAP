from pathlib import Path

import scrapy
from scrapy.crawler import CrawlerProcess

class ZAPSpider(scrapy.Spider):
    name = "zapspider"

    def __init__(self, urls : list, *args, **kwargs):
        super(ZAPSpider, self).__init__(*args, **kwargs)
        self.urls = urls

    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = f"quotes-{page}.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")
    
    def closed(self, reason):
        pass

def runspider(urls : list[str]):
    process = CrawlerProcess(
        settings={
            "FEEDS": {
                "items.json": {"format": "json"},
            },
        }   
    )

    process.crawl(ZAPSpider, urls)
    process.start()