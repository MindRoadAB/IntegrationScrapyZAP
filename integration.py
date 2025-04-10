from zapcrawler.zapcrawler.spiders.zapspider import runspider
from zap import Zap
from urllib.parse import urlparse

class Integrator:
    def __init__(self, urls : list, apikey : str):
        self.seed_urls = urls
        self.crawler_result = []
        self.zap = Zap(apikey=apikey)

    def execute(self):
        confirmed_urls = self.crawl()
        self.attack(confirmed_urls)

    def crawl(self):
        self.crawler_result = list(set(runspider(self.seed_urls)))

        return self.double_check_crawler_result()

    def attack(self, confirmed_urls):
        #self.zap.active_scan(confirmed_urls)

    """
    Funktionen ansvarar för att dubbelkolla så inga URL:er förekommer utanför angivna domän.
    Utföra attacker på icke verifierade sidor är ett allvarligt övertramp.
    """
    def double_check_crawler_result(self):
        confirmed_urls = []

        for url in self.crawler_result:
            base_url = extract_domain(url)

            for seed_url in self.seed_urls:
                if base_url == extract_domain(seed_url):
                    confirmed_urls.append(url)
                    break

        return confirmed_urls

def extract_domain(url):
    return urlparse(url).netloc