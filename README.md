# IntegrationScrapyZAP
Projekt där en egen crawler med funktionalitet att hantera AJAX integrerats med OWASP ZAP.
Crawlern är byggd i Scrapy och använder Playwright för att rendera JS och möjliggöra interaktion.

# Grundkrav
För att kunna köra projektet behövs ett antal program.

* OWASP ZAP - https://www.zaproxy.org/download/
* Scrapy - https://github.com/scrapy/scrapy
* Playwright - https://github.com/scrapy-plugins/scrapy-playwright (Plugin för Scrapy)

Det finns även en requirements för samtliga python-plugins, se requirements.txt.

# Setup/installation
Kör `git clone --recursive https://github.com/MindRoadAB/IntegrationScrapyZAP.git` för att få med Scrapy som är satt som submodule. Ladda sedan  ner och installera OWASP ZAP.

Skapa sedan en vm `python -m venv <namn>` och sedan aktivera den `source <filepath>`. Stå sedan i mappen med requirements.txt och kör `pip install -r requirements.txt`. Nu borde allt som behövs vara installerat och redo.