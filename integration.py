from zapcrawler.zapcrawler.spiders.zapspider import runspider

class Integrator:
    def __init__(self, urls : list):
        self.urls = urls

    def execute(self):
        self.crawl()
        self.attack()
        self.analyze()

    def crawl(self):
        runspider(self.urls)

    def attack(self):
        pass

    def analyze(self):
        pass