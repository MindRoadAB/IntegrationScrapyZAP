from zapcrawler.zapcrawler.spiders.zapspider import runspider
from zapv2 import ZAPv2
import time
from pprint import pprint

class Integrator:
    def __init__(self, urls : list, apikey : str):
        self.urls = urls
        self.crawler_result = []
        self.zap = ZAPv2(apikey=apikey, proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'})

    def execute(self):
        self.crawl()
        self.attack()
        self.analyze()

    def crawl(self):
        self.crawler_result = list(set(runspider(self.urls)))

    def attack(self):
        print(self.crawler_result)

        #Titta in scan-policy

        self.crawler_result = ["https://public-firing-range.appspot.com/"]

        print("Utför aktiv attack.")
        for url in self.crawler_result:
            self.zap.urlopen(url)
            scan = self.zap.ascan.scan(url=url)
            
            while (int(self.zap.ascan.status(scan)) < 100):
                time.sleep(5)

            print("RESULTAT")
            print('Hosts: {}'.format(', '.join(self.zap.core.hosts)))
            print('Alerts: ')
            pprint(self.zap.core.alerts(baseurl=url))
            

    def analyze(self):
        pass