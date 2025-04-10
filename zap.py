from zapv2 import ZAPv2
import time
from pprint import pprint

class Zap:
    def __init__(self, apikey):
        self.zap = ZAPv2(apikey=apikey, proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'})

    def active_scan(self, urls):
        for url in urls:
            self.zap.urlopen(url)
            scan = self.zap.ascan.scan(url=url, scanpolicyname="Injection")
            
            while (int(self.zap.ascan.status(scan)) < 100):
                time.sleep(5)

            print("RESULTAT")
            print('Hosts: {}'.format(', '.join(self.zap.core.hosts)))
            print('Alerts: ')
            pprint(self.zap.core.alerts(baseurl=url))