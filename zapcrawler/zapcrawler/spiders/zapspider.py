from pathlib import Path

import scrapy

from scrapy_playwright.page import PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from parsel import Selector
from urllib.parse import urljoin, urlparse
import asyncio
from collections import deque

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
        self.current_state_elements = []
        self.visited_urls = urls.copy()
        self.max_depth = 5

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
        await self.mutationobserver_setup(page)

        interactive_elements_dict = await self.find_all_interactive_elements(page)

        current_depth = 0
        await self.interact_with_page(page, interactive_elements_dict, current_depth, self.max_depth)        

        await page.close()

    """
    Interaktionsfunktioner
    """
    def login(self):
        pass

    def infinite_scroll(self):
        pass

    async def find_all_interactive_elements(self, page):
        interactive_elements_dict = {}

        interactive_elements_dict["fillables"] = await self.find_fillables(page)
        interactive_elements_dict["clickables"] = await self.find_clickables_from_page(page)

        return interactive_elements_dict

    async def interact_with_page(self, page, interactive_elements_dict, depth, max_depth):
        #Fullösning för att undvika oändlig rekursion
        if depth > max_depth:
            return
        
        await self.fill_fillables(page, interactive_elements_dict["fillables"])
        await self.click_clickables(page, interactive_elements_dict["clickables"])


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

        fillables = deque()
        for selector in fillable_types:
            elements = await page.query_selector_all(selector)
            fillables.extend(elements)
        
        return fillables

    async def fill_fillables(self, page, fillables):
        text = "test"

        while fillables:
            fillable = fillables.popleft()

            try:
                if await fillable.is_visible() and await fillable.is_enabled():
                    await fillable.fill(text)
            except Exception as e:
                pass

    async def find_clickables_from_page(self, page):
        selectors = ["button", '[role="button"]', "a", "[onclick]"]
        clickable_elements = []

        for selector in selectors:
            locs = page.locator(selector)
            count = await locs.count()
            for i in range(count):
                clickable_elements.append(locs.nth(i))

        self.current_state_elements = clickable_elements.copy()

        return clickable_elements

    async def click_clickables(self, page, clickable_elements):
        loops = 0
        max_loops = 50
        clickable_elements_deque = deque(clickable_elements)

        while clickable_elements_deque and loops < max_loops:
            loops += 1
            element = clickable_elements_deque.popleft()

            try:
                await element.click(timeout=750)    
                await page.wait_for_load_state("networkidle")
                print("\nKNAPP TRYCKT: ", element)

            except Exception as e:
                print("\nCATCH: ", e)
                clickable_elements_deque.append(element)

        self.current_state_elements = []

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

    async def mutationobserver_setup(self, page):
        await page.evaluate("""
            () => {
                window.__newElements = [];
                if (window.__observer) window.__observer.disconnect();
                window.__observer = new MutationObserver(mutations => {
                    for (const mutation of mutations) {
                        for (const node of mutation.addedNodes) {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                window.__newElements.push(node);
                            }
                        }
                    }
                });
                window.__observer.observe(document.body, { childList: true, subtree: true });
            }
            """)
        
    async def get_new_elements(self, page):
        return await page.evaluate("""
            () => {
                const nodes = window.__newElements || [];
                const results = [];
                for (const el of nodes) {
                    if (el.outerHTML) {
                        results.push({ html: el.outerHTML, tag: el.tagName, text: el.innerText });
                    }
                }
                window.__newElements = [];
                return results;
            }
            """)


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

Antecknade problem
* - inte trycker på element som är aktiva, behöver göra en check
* - Hitta vilka element som är klickabara
* - Säkerställa så att man inte följer länkar till andra sidor utanför domän
* - Måste lyssna på nätverket för att plock aupp AJAX-anrop
* - Klicka på element i rätt ordning
* - Upptäcka hur DOM:en eventuellt ändras efter ett klick, hämta dessa nya element och endast klicka på dem
* - Hålla koll på state så man inte gör samma sak flera gångar
    

* - Crawling A JAX -Based Web Applications through Dynamic Analysis of User Interface State Changes
* - Crawling Rich Internet Applications: The State of the Art
* - A Comparative Study of Web Application Security Parameters: Current Trends and Future Directions
"""