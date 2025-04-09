from pathlib import Path

import scrapy

from scrapy_playwright.page import PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

#from selenium import webdriver
#from selenium.webdriver.firefox.options import Options

class ZAPSpider(scrapy.Spider):
    name = "zapspider"

    custom_settings = {
        "BOT_NAME" : "zapcrawler",
        "SPIDER_MODULES" : ["zapcrawler.spiders"],
        "NEWSPIDER_MODULE" : "zapcrawler.spiders",
        "DOWNLOAD_HANDLERS" : {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },

        "TWISTED_REACTOR" : "twisted.internet.asyncioreactor.AsyncioSelectorReactor",

        "PLAYWRIGHT_BROWSER_TYPE" : 'firefox',

        "PLAYWRIGHT_LAUNCH_OPTIONS" : {
                "headless": True,
        },
        "CONCURRENT_REQUESTS": 1, #Problem med att få playwright att hantera flera request samtidigt därav max 1 concurrent request.
        "ROBOTSTXT_OBEY" : True,
        "FEED_EXPORT_ENCODING" : "utf-8",
        "USER_AGENT" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }

    def __init__(self, urls : list, *args, **kwargs):
        super(ZAPSpider, self).__init__(*args, **kwargs)
        self.urls = urls
        self.result = []

    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={"playwright": True})

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = f"quotes-{page}.html"
        Path(filename).write_bytes(response.body)
        self.result.append(response.body)

def runspider(urls : list[str]):
    process = CrawlerProcess(get_project_settings())

    crawler = process.create_crawler(ZAPSpider)

    process.crawl(crawler, urls)
    process.start()

    return crawler.spider.result


"""
,
				playwright_include_page = True, 
				playwright_page_methods =[PageMethod('wait_for_selector', 'div.quote')]
"""

"""
#SELENIUM-START
        #Kod under arbete
        driver = webdriver.Firefox(options=setup_options_selenium())

        driver.quit()
        #SELENIUM-END

#Här sätter användare upp sin egna options. 
def setup_options_selenium():
    options = webdriver.FirefoxOptions()
    options.binary_location = "/usr/bin/firefox"
    options.headless = False
    options.add_argument("-profile")
    options.add_argument('/home/simlu/snap/firefox/common/.mozilla/firefox/n6yfipfz.selenium_profile')

    return options
"""