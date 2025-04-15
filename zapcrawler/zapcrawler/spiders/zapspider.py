from pathlib import Path

import scrapy

from scrapy_playwright.page import PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from parsel import Selector
from urllib.parse import urljoin, urlparse
import asyncio

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
                "headless": False,
        },
        "PLAYWRIGHT_RESTART_DISCONNECTED_BROWSER" : True,
        "CONCURRENT_REQUESTS": 256,
        "ROBOTSTXT_OBEY" : True,
        "FEED_EXPORT_ENCODING" : "utf-8",
        "USER_AGENT" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }

    def __init__(self, urls, mode="classic", *args, **kwargs):
        super(ZAPSpider, self).__init__(*args, **kwargs)
        self.urls = urls.copy()
        self.mode = mode
        self.entrypoints = []
        self.visited_urls = urls.copy()

    def start_requests(self):
        for url in self.urls:
            yield from self.crawl(url)

    
    """
    Crawlerfunktioner
    """
    def crawl(self, url):
        if self.mode == "classic":
            yield from self.crawl_classic(url)
        elif self.mode == "js":
            yield from self.crawl_js(url)
        elif self.mode == "ajax":
            yield from self.crawl_ajax(url)

    def crawl_classic(self, url):
        yield scrapy.Request(url=url, callback=self.parse)

    def crawl_js(self, url):
        yield scrapy.Request(
            url=url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_page_methods" : [
                    PageMethod("wait_for_load_state", "networkidle")
                ]
            }
        )

    def crawl_ajax(self, url):
        yield scrapy.Request(
            url=url,
            callback=self.parse_ajax,
            meta={
                "playwright": True,
                "playwright_include_page" : True,
                "playwright_page_methods" : [
                    PageMethod("wait_for_load_state", "networkidle")
                ]
            }
        )

    """
    Parsefunktioner
    """
    def parse(self, response):
        selector = Selector(text=response.text)

        yield from self.extract_urls(selector, response.url)

        #Extrahera endpoints
        self.find_forms(selector, response.url)

    async def parse_ajax(self, response):
        page = response.meta["playwright_page"]
        page.on("response", lambda response: asyncio.create_task(self.handle_response_ajax(response))) #Lyssnare efter AJAX-anrop
        
        await self.interact_with_page(page)        

        await page.close()

    """
    Interaktionsfunktioner
    """
    def login(self):
        pass

    def infinite_scroll(self):
        pass

    async def interact_with_page(self, page):
        fillables = await self.find_fillables(page)
        await self.fill_fillables(page, fillables)

        clickable_elements = await self.find_clickables_from_page(page)
        await self.click_clickables(page, clickable_elements)

    async def find_fillables(self, page):
        fillable_types = [
            "input[type='text']",
            "input[type='email']",
            "input[type='search']",
            "input[type='password']",
            "input:not([type])",
            "textarea",
            "[contenteditable='true']"
        ]

        fillables = []
        for selector in fillable_types:
            elements = await page.query_selector_all(selector)
            fillables.extend(elements)
        
        return fillables

    async def fill_fillables(self, page, fillables):
        text = "test"

        for fillable in fillables:
            try:
                if await fillable.is_visible() and await fillable.is_enabled():
                    await fillable.fill(text)
            except Exception as e:
                pass

    async def find_clickables_from_page(self, page):
        clickable_elements = []

        buttons = await page.query_selector_all("button")
        clickable_elements.extend(buttons)

        role_buttons = await page.query_selector_all('[role="button"]')
        clickable_elements.extend(role_buttons)

        links = await page.query_selector_all("a")
        clickable_elements.extend(links)

        onclick_elements = await page.query_selector_all('[onclick]')
        clickable_elements.extend(onclick_elements)

        return clickable_elements

    async def click_clickables(self, page, clickable_elements):
        for element in clickable_elements:
            try:
                if await element.is_visible() and await element.is_enabled():
                    #await page.evaluate("""
                    #    window.__newElements = [];
                    #    const observer = new MutationObserver(mutations => {
                    #        for (const mutation of mutations) {
                    #           for (const node of mutation.addedNodes) {
                    #               if (node.nodeType === Node.ELEMENT_NODE) {
                    #                   window.__newElements.push(node.outerHTML);
                    #               }
                    #            }
                    #       }
                    #   });
                    #   observer.observe(document.body, { childList: true, subtree: true });
                    #""")
                    await element.click(timeout=500)

                    #new_elements = await page.evaluate("window.__newElements")
                    #print("\n", new_elements)
            except Exception as e:
                pass

    """
    Scrapefunktioner
    """
    #Hämtar ut url:er inom samma domän för crawling.
    def extract_urls(self, selector, base_url):
        for rel_url in selector.css("a::attr(href)").getall():
            entrypoint = urljoin_domain(base_url, rel_url)
            self.add_entrypoint(base_url, entrypoint)
            if ensure_valid_url(base_url, entrypoint) and entrypoint not in self.visited_urls:
                self.visited_urls.append(entrypoint)
                yield from self.crawl(entrypoint)
            
    def find_forms(self, selector, base_url):
        for form in selector.css("form"):
            action = form.css("::attr(action)").get()
            entrypoint = urljoin_domain(base_url, action)
            self.add_entrypoint(base_url, entrypoint)

    """
    Stödfunktioner
    """
    def add_entrypoint(self, base_url, entrypoint):
        if ensure_valid_url(base_url, entrypoint):
            self.entrypoints.append(entrypoint)

    async def handle_response_ajax(self, response):
        url = response.url
        try:
            body = await response.text()
            if "application/json" in response.headers.get("content-type", ""):
                self.entrypoints.append(url)
        except Exception as e:
            pass


"""
Övrigafunktioner
"""

def runspider(urls, mode):
    process = CrawlerProcess(get_project_settings())

    crawler = process.create_crawler(ZAPSpider)

    process.crawl(crawler, urls, mode)
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
PLAN med ledande frågor.

Vilka interaktionsfunktioner behöver jag?
    Svar:
        Klicka  - NOT DONE
        login   - NOT DONE
        scrolla - NOT DONE

Hur ska jag hantera states (veta var jag har varit och inte)?
    Problembeskrivning: Om jag inte kan tracka detta så är det stor risk för onödigt arbete samt oändliga loopar.
    Svar: 

Hur ska jag kunna lyssna på AJAX-förfrågningar
    Svar:


"""