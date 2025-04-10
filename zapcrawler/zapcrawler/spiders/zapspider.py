from pathlib import Path

import scrapy

from scrapy_playwright.page import PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from parsel import Selector
from urllib.parse import urljoin, urlparse

#from selenium import webdriver
#from selenium.webdriver.firefox.options import Options

class ZAPSpider(scrapy.Spider):
    name = "zapspider"

    custom_settings = {
        "BOT_NAME" : "zapcrawler",
        "SPIDER_MODULES" : ["zapcrawler.spiders"],
        "NEWSPIDER_MODULE" : "zapcrawler.spiders",
        "DEPTH_LIMIT" : 5,

        "DOWNLOAD_HANDLERS" : {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },

        "TWISTED_REACTOR" : "twisted.internet.asyncioreactor.AsyncioSelectorReactor",

        "PLAYWRIGHT_BROWSER_TYPE" : 'firefox',

        "PLAYWRIGHT_LAUNCH_OPTIONS" : {
                "headless": True,
        },
        "PLAYWRIGHT_RESTART_DISCONNECTED_BROWSER" : True,
        "CONCURRENT_REQUESTS": 256,
        "ROBOTSTXT_OBEY" : True,
        "FEED_EXPORT_ENCODING" : "utf-8",
        "USER_AGENT" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }

    def __init__(self, urls : list, *args, **kwargs):
        super(ZAPSpider, self).__init__(*args, **kwargs)
        self.urls = urls.copy()
        self.entrypoints = []
        self.visited_urls = urls.copy()

    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={
                "playwright": True
                })

    def parse(self, response):
        selector = Selector(text=response.text)

        yield from self.extract_urls(selector, response.url)

        #Extrahera endpoints
        self.find_forms(selector, response.url)

    #Hämtar ut url:er inom samma domän för crawling.
    def extract_urls(self, selector, base_url):
        for rel_url in selector.css("a::attr(href)").getall():
            entrypoint = urljoin_domain(base_url, rel_url)
            self.add_entrypoint(base_url, entrypoint)
            if ensure_valid_url(base_url, entrypoint) and entrypoint not in self.visited_urls:
                self.visited_urls.append(entrypoint)
                yield scrapy.Request(url=entrypoint, callback=self.parse, meta={
                    "playwright": True
                    })
            
    def find_forms(self, selector, base_url):
        for form in selector.css("form"):
            action = form.css("::attr(action)").get()
            entrypoint = urljoin_domain(base_url, action)
            self.add_entrypoint(base_url, entrypoint)

    def add_entrypoint(self, base_url, entrypoint):
        if ensure_valid_url(base_url, entrypoint):
            self.entrypoints.append(entrypoint)


def runspider(urls : list[str]):
    process = CrawlerProcess(get_project_settings())

    crawler = process.create_crawler(ZAPSpider)

    process.crawl(crawler, urls)
    process.start()

    return crawler.spider.entrypoints

def urljoin_domain(base_url, rel_url):
    if rel_url is None or rel_url == "":
        return None
    else:
        return rel_url if rel_url.startswith("http://") or rel_url.startswith("https://") else urljoin(base_url, rel_url)
    
def ensure_same_domain(url_one, url_two):
    return True if urlparse(url_one).netloc == urlparse(url_two).netloc else False

def ensure_valid_url(base_url, entrypoint):
    return entrypoint is not None and ensure_same_domain(base_url, entrypoint)

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