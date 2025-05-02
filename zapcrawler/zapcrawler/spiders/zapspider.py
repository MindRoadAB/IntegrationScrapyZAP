from pathlib import Path

import scrapy

from scrapy_playwright.page import PageMethod
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from parsel import Selector
from urllib.parse import urljoin, urlparse
import asyncio
from collections import deque

import traceback

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
        page.on("console", lambda msg: print(f"[console] {msg.type}: {msg.text}"))
        page.on("response", lambda response: asyncio.create_task(self.handle_response_ajax(response))) #Lyssnare efter AJAX-anrop        
        await self.mutationobserver_setup(page)
        await self.state_handler(page)

        #Hantering av navigation
        #await self.navigation_handler(page)
        await page.route("**/*", self.navigation_handler)
        page.on('popup', lambda new_page: self.new_page_or_popup_handler(new_page))

        interactive_elements_dict = await self.find_all_interactive_elements(page)

        current_depth = 1
        await self.interact_with_page(page, interactive_elements_dict, current_depth)

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
        body_element = page.locator("body *:not(style)")
        interactive_elements_dict["clickables"] = await self.find_clickables_from_page(body_element)

        return interactive_elements_dict

    async def interact_with_page(self, page, interactive_elements_dict, depth):
        #Fullösning för att undvika oändlig rekursion
        if depth > self.max_depth:
            return
        
        #await self.fill_fillables(page, interactive_elements_dict["fillables"])
        await self.click_clickables(page, depth, interactive_elements_dict["clickables"])


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
        selectors = ["button", "a", '[role="button"]', "[onclick]", '[aria-label="Close Dialog"]']
        clickable_elements = []

        for selector in selectors:
            locs = page.locator(selector)
            count = await locs.count()
            for i in range(count):
                clickable_elements.append(locs.nth(i))

        return clickable_elements

    async def click_clickables(self, page, depth, clickable_elements):
        loops = 0
        overlay_exist = await has_overlay(clickable_elements)
        if overlay_exist:
            overlay_element, clickable_elements = await remove_overlay_from_list(clickable_elements)
        clickable_elements_deque = deque(clickable_elements)

        while clickable_elements_deque and loops < (len(clickable_elements_deque) * 3):
            loops += 1
            element = clickable_elements_deque.popleft()

            try:
                if await element.is_visible() and await element.is_enabled():
                    await element.click(timeout=750)    
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_load_state("domcontentloaded")

                    new_elements = await self.get_new_elements(page)
                    xpath_strings = extract_interactive_xpath_string(new_elements)
                    new_clickables = await acquire_page_locators_from_xpath(xpath_strings, page)

                    if len(new_clickables) > 0:
                        await self.interact_with_page(page, {"clickables" : new_clickables}, (depth+1))
                else:
                    clickable_elements_deque.append(element)

            except Exception as e:
                await page.wait_for_load_state("networkidle")
                await page.wait_for_load_state("domcontentloaded")
                clickable_elements_deque.append(element)

        if overlay_exist:
            await close_overlay(page, overlay_element)

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
                        const target = mutation.target;

                        if (mutation.type === "childList") {
                            for (const node of mutation.addedNodes) {
                                if (node.nodeType === Node.ELEMENT_NODE) {
                                    window.__newElements.push(node);
                                }
                            }
                        }

                        if (
                            mutation.type === "attributes" &&
                            target.classList.contains("mat-drawer") &&
                            target.classList.contains("mat-sidenav") &&
                            target.classList.contains("mat-drawer-opened")
                        ) {
                            window.__newElements.push(target);
                        }
                    }
                });

                window.__observer.observe(document.body, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    attributeFilter: ["class", "style"]
                });
            }
        """)

    async def state_handler(self, page):
        await page.evaluate("""
            () => {                            
                document.addEventListener("click", function (event) {
                    const target = event.target;
                    const anchor = target.closest("a");
                    const button = target.closest("button");

                    window.__blockedNavigations = window.__blockedNavigations || [];

                    // Blockera a[href]
                    if (anchor && anchor.getAttribute("href")) {
                        event.preventDefault();
                        event.stopPropagation();
                        const href = anchor.href;
                        console.log("🔗 Blocked navigation to (href):", href);
                        window.__blockedNavigations.push({ type: "href", value: href });
                        return;
                    }

                    // Blockera a[routerLink]
                    if (anchor && anchor.hasAttribute("routerlink")) {
                        event.preventDefault();
                        event.stopPropagation();
                        const route = anchor.getAttribute("routerlink");
                        console.log("🧭 Blocked navigation to (routerLink on <a>):", route);
                        window.__blockedNavigations.push({ type: "routerLink", value: route });
                        return;
                    }

                    // Blockera button[routerLink]
                    if (button && button.hasAttribute("routerlink")) {
                        event.preventDefault();
                        event.stopPropagation();
                        const route = button.getAttribute("routerlink");
                        console.log("🧭 Blocked navigation to (routerLink on <button>):", route);
                        window.__blockedNavigations.push({ type: "routerLink", value: route });
                        return;
                    }
                }, true);
            }
        """)


    async def navigation_handler(self, route, request):
        if request.is_navigation_request():
            print("\n\nNAVIGATION BROTHER: ", request.url, "\n\n")

    async def new_page_or_popup_handler(self, page):
        if any(ensure_same_domain(url, page.url) for url in self.urls):
            print("\nPOPUP URL: ", page.url)
        else:
            await page.close()
        
    async def get_new_elements(self, page):
        return await page.evaluate("""
            () => {
                function findClickableElements(root) {
                    const clickable = [];
                    const elements = root.querySelectorAll('*');

                    for (const el of elements) {
                                   
                        if (
                            el.tagName.toLowerCase() === 'button' ||
                            (el.tagName.toLowerCase() === 'a' && el.hasAttribute('href')) ||                        
                            el.getAttribute('role') === 'button' ||
                            el.hasAttribute('onclick') ||
                            el.getAttribute('aria-label') === 'Close Dialog' ||
                            el.tagName.toLowerCase() === 'sidenav'
                        ) {
                            clickable.push({
                                html: el.outerHTML,
                                tag: el.tagName,
                                text: el.innerText
                            });
                        }
                    }
                    return clickable;
                }

                const nodes = window.__newElements || [];
                const results = [];

                for (const node of nodes) {
                    results.push(...findClickableElements(node));
                }

                window.__newElements = [];
                return results;
            }
        """)
    #(el.tagName.toLowerCase() === 'a' && el.hasAttribute('href')) ||


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

def extract_interactive_xpath_string(elements):
    xpath_strings = set()
    
    for element in elements:
        selector = Selector(text=element['html'])

        # Scrapy Selector sätter detta i HTML-trädet (<html><body>...</body></html>) så vi hämtar ut det faktiska elementet
        selector_element = selector.xpath('//body/*[1]')[0]
        
        tag = selector_element.root.tag
        xpath_string = f'//{tag}'

        classes = selector_element.root.attrib.get('class')
        if classes:
            xpath_string += f'[contains(@class, "{classes.split()[0]}")]'

        for attr, value in selector_element.root.attrib.items():
            if attr != 'class':
                xpath_string += f'[@{attr}="{value}"]'

        xpath_strings.add(xpath_string)

    return list(xpath_strings)

async def acquire_page_locators_from_xpath(xpath_strings, page):
    list_of_locators = []

    xpath_strings.sort(key=lambda x: 'close-dialog' in x) #Ser till så att close-dialog alltid trycks sist.

    for xpath_string in xpath_strings:
        locator = page.locator(xpath_string)
        count = await locator.count()
        for i in range(count):
            list_of_locators.append(locator.nth(i))

    return list_of_locators

async def has_overlay(list_of_elements):
    for element in list_of_elements:
        if await element.count() > 0 and await element.first.evaluate("el => el.tagName.toLowerCase() === 'sidenav'"):
            return True

    return False

async def remove_overlay_from_list(list_of_elements):
    overlay_element = 0

    for i, element in enumerate(list_of_elements):
        is_overlay = await element.first.evaluate("el => el.tagName.toLowerCase() === 'sidenav'")
        if is_overlay:
            overlay_element = list_of_elements.pop(i)
            break

    return overlay_element, list_of_elements

async def close_overlay(page, overlay_element):
    if(await has_transition_occured(overlay_element)):
        position_dict = await overlay_element.bounding_box()

        x_pos = position_dict["x"]
        y_pos = position_dict["y"]
        width = position_dict["width"]
        out_of_box_modifier = 25

        if x_pos is not None and y_pos is not None and width is not None:
            await page.mouse.click(
                (x_pos + width + out_of_box_modifier),
                (y_pos + out_of_box_modifier)
            )

async def has_transition_occured(element, max_attempts=5, interval_s=0.25):
    previous_position = await element.bounding_box()

    for _ in range(max_attempts):
        await asyncio.sleep(interval_s)
        current_position = await element.bounding_box()

        if previous_position == current_position:
            return True
        
        previous_position = current_position

    return False

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
* - hantera transistions?!
* - Skiftar URL utan att trigga request med mera
* - Borde kanske ha jobbat med JavaScript push- och popstate?
    

* - Crawling A JAX -Based Web Applications through Dynamic Analysis of User Interface State Changes
* - Crawling Rich Internet Applications: The State of the Art
* - A Comparative Study of Web Application Security Parameters: Current Trends and Future Directions
"""