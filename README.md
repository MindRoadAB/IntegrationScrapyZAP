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
Kör `git clone --recursive https://github.com/MindRoadAB/IntegrationScrapyZAP.git` för att få med Scrapy som är satt som submodule. Ladda sedan ner och installera OWASP ZAP.

Skapa sedan en vm `python -m venv <namn>` och sedan aktivera den `source <filepath>`. Stå sedan i mappen med requirements.txt och kör `pip install -r requirements.txt`. Nu borde allt som behövs vara installerat och redo.

# Information
Detta är en mycket begränsad crawler som testat frågan om det är möjligt och vad för effekt integrationen av en extern AJAX crawler har på OWASP ZAP.
Den är byggd att fungera tillräckligt på plattformen OWASP Juice Shop -> https://github.com/juice-shop/juice-shop.

Använd crawlingteknik är eventbaserad crawling vilket mycket kortfattat beskrivs nedan:
1. Inhämta interagerbara element
2. Interagera med elementen
3. Kolla hur DOM:en uppdaterats och inhämta eventuella nya interagerbara element

# Körning
För att kunna köra crawlern, starta först ZAP så det är igång. Kör sedan följande: `python main.py -u <URL> -a <API-key ZAP>`. Detta startar och kör crawlern.
Det finns tre flaggor programmet kan hantera:
* -a -> API-key för att kunna använda ZAP:s API.
* -u -> Vilken url som ska crawlas.
* -m -> Vilken mode, det finns ajax, classic och js. Ajax är satt som default.