from zapcrawler.zapcrawler.spiders.zapspider import runspider
from zapv2 import ZAPv2
import time
from pprint import pprint

class Integrator:
    def __init__(self, urls : list, apikey : str):
        self.urls = urls
        self.crawler_result = []
        self.zap = ZAPv2(apikey=apikey)

    def execute(self):
        self.crawl()
        self.attack()
        self.analyze()

    def crawl(self):
        self.crawler_result = list(set(runspider(self.urls)))

    def attack(self):
        print(self.crawler_result)

        print("Utför aktiv attack.")
        for url in self.crawler_result:
            self.zap.urlopen(url)
            scan = self.zap.ascan.scan(url=url)
            print("\n",scan,"\n")
            
            while (int(self.zap.ascan.status(scan)) < 100):
                print ('Scan progress %: {}'.format(self.zap.ascan.status(scan)))
                time.sleep(5)

            print("RESULTAT")
            pprint (self.zap.core.alerts())
            

    def analyze(self):
        pass