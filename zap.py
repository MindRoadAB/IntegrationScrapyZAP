from zapv2 import ZAPv2
import time
import matplotlib.pyplot as plt
import os
from datetime import datetime

class Zap:
    def __init__(self, apikey):
        self.zap = ZAPv2(apikey=apikey, proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'})


    def run_spiders(self, url="http://localhost:3000"):
        session_catalog = self.ensure_zap_session_catalog()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        result_custom = self.run_custom_crawler(url)
        session_name = os.path.join(session_catalog, f"custom_{timestamp}.session")
        self.zap.core.save_session(name=session_name, overwrite=True)

        result_ajax_spider = self.run_ajax_spider(url)
        session_name = os.path.join(session_catalog, f"ajax_{timestamp}.session")
        self.zap.core.save_session(name=session_name, overwrite=True)

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
        # Lägre fall för enklare matchning
        url_lower = url.lower()

        # Filändelser vi inte bryr oss om
        uninteresting_extensions = (
            ".js", ".css", ".jpg", ".jpeg", ".png", ".gif", ".svg",
            ".woff", ".woff2", ".ttf", ".eot", ".ico", ".mp4", ".webp",
            ".ini", ".xml", ".pem", ".key", ".sql", ".md", ".log",
            ".map", ".pdf", ".csv", ".yml", ".rss", ".scss", ".sass",
            ".txt", ".mp3", ".avi", ".mov", ".zip", ".rar", ".7z",
        )

        # Filer som kan innehålla känslig information men inte är endpoints
        sensitive_files = (
            ".env", ".htaccess", "id_rsa", "id_dsa", "myserver.key",
            "server.key", "privatekey.key", "config.yml", "config.json",
            ".ds_store", "composer.lock", "package-lock.json",
            "phpinfo.php", "info.php", "elmah.axd", "trace.axd"
        )

        # Kataloger som är versionskontroll, IDE-konfiguration etc.
        blacklisted_paths = (
            "/.git", "/.svn", "/.hg", "/.bzr", "/.idea", "/_wpeprivate",
            "/cvs", "/bitkeeper", "/node_modules", "/bower_components",
            "/vendor/", "/backup", "/backups", "/temp", "/cache", "/logs"
        )

        # Speciella strängar som indikerar runtime eller dev-artefakter
        blacklisted_keywords = (
            "socket.io", "runtime", "polyfills", "vendor", "static",
            "webpack", "favicon", "robots.txt", "sitemap.xml",
            "assets/", "fonts/", "images/", "scripts/", "styles/",
            "public/", "uploads/", "media/", "docs/", "examples/"
        )

        if url_lower.endswith(uninteresting_extensions):
            return True

        if any(s in url_lower for s in sensitive_files):
            return True

        if any(p in url_lower for p in blacklisted_paths):
            return True

        if any(k in url_lower for k in blacklisted_keywords):
            return True

        return False
    
    def compare_spiders(self, custom_endpoints, ajax_endpoints):
        set_custom = set(custom_endpoints)
        set_ajax = set(ajax_endpoints)

        labels = ['Custom Crawler', 'AJAX Spider']
        counts = [len(set_custom), len(set_ajax)]

        plt.figure(figsize=(6, 5))
        bars = plt.bar(labels, counts, color=['#ff9999', '#66b3ff'])
        plt.title('Antal upptäckta endpoints per crawler')
        plt.ylabel('Antal endpoints')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.5, int(yval), ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig("endpoint_comparison_simple.png")
        print("✅ Graf sparad som 'endpoint_comparison_simple.png'")

    def ensure_zap_session_catalog(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        session_dir = os.path.join(base_dir, "zap_sessions")
        os.makedirs(session_dir, exist_ok=True)

        return session_dir