from zapv2 import ZAPv2
import time
import matplotlib.pyplot as plt
from matplotlib_venn import venn2

class Zap:
    def __init__(self, apikey):
        self.zap = ZAPv2(apikey=apikey, proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'})


    def run_spiders(self, url="http://localhost:3000"):
        result_custom = self.run_custom_crawler(url)
        result_ajax_spider = self.run_ajax_spider(url)

        self.compare_spiders(result_custom, result_ajax_spider)

    def active_scan(self, url="http://localhost:3000"):
        sites = self.zap.core.sites
        filtered_urls = []
        for site in sites:
            if site == url:
                print(f"Scanning site: {site}")

                scan_id = self.zap.ascan.scan(site, scanpolicyname="Default Policy")
                    
                while int(self.zap.ascan.status(scan_id)) < 100:
                    time.sleep(3)
                

                urls = self.zap.core.urls(site)
                number = 1
                filtered_urls = self.filter_result(urls)

                print("Url och endpoints hittade.")
                for url in filtered_urls:
                    print("\nURL ",number,": ", url)
                    number += 1
            
        print("✅ All scanning done.")
        return filtered_urls

    def run_ajax_spider(self, url="http://localhost:3000"):
        self.zap.core.new_session(name='AJAX SPIDER', overwrite=True)

        self.zap.ajaxSpider.scan(url)

        while self.zap.ajaxSpider.status != 'stopped':
            time.sleep(2)

        return self.active_scan(url)

    def run_custom_crawler(self, url="http://localhost:3000"):
        return self.active_scan(url)        

    def filter_result(self, urls):
        filtered_result = list(set([url.rstrip("/") for url in urls if not self.is_irrelevant(url)]))

        filtered_result.sort()
        return filtered_result

    def is_irrelevant(self, url):
        uninteresting_extensions = (
            ".js", ".css", ".jpg", ".jpeg", ".png", ".gif", ".svg",
            ".woff", ".woff2", ".ttf", ".eot", ".ico", ".mp4", ".webp"
        )

        if url.lower().endswith(uninteresting_extensions):
            return True
        
        if "/socket.io" in url:
            return True
        
        if "runtime" in url or "polyfills" in url or "vendor" in url:
            return True
        return False
    
    def compare_spiders(self,custom_endpoints, ajax_endpoints):
        set_custom = set(custom_endpoints)
        set_ajax = set(ajax_endpoints)

        # Endast i custom, endast i ajax, gemensamma
        only_custom = set_custom - set_ajax
        only_ajax = set_ajax - set_custom
        common = set_custom & set_ajax

        labels = ['Endast Custom Crawler', 'Endast AJAX Spider', 'Gemensamma']
        counts = [len(only_custom), len(only_ajax), len(common)]

        # Plot
        plt.figure(figsize=(8, 6))
        bars = plt.bar(labels, counts, color=['#ff9999', '#66b3ff', '#99ff99'])
        plt.title('Jämförelse av upptäckta endpoints')
        plt.ylabel('Antal endpoints')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Lägg till etiketter ovanpå staplarna
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.5, int(yval), ha='center', va='bottom')

        # Spara grafen som PNG
        plt.tight_layout()
        plt.savefig("endpoint_comparison.png")
        print("✅ Graf sparad som 'endpoint_comparison.png'")