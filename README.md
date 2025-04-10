# IntegrationScrapyZAP
Projekt där Scrapy integreras med OWASP ZAP.

# Grundkrav
För att kunna köra projektet behövs ett antal program.

* OWASP ZAP - https://www.zaproxy.org/download/
* Scrapy - https://github.com/scrapy/scrapy
* Selenium
* Geckodriver, för firefox
* Playwright

# Setup/installation
To Come

# Plan för det fortsatta arbetet
* Skapa en scan-policy - CHECK (Injection)
* Implementera att följa URL:er i crawler - CHECK
* Bryta ut ZAP-funktioner i egen klass - CHECK
* Lägga in funktionalitet för att dubbelkolla så inga felaktiga URL:er kommer tillbaka från crawler - CHECK
* Lägga till flagga -m --mode för att kunna välja vilken sorts crawling som ska utföras - CHECK
* Lägga till parsning och extraktion av mer än bara forms - UNDER ARBETE
* Lägga till AJAX-hantering - UNDER ARBETE (STORT ARBETE)
* VID TID! - Liten chans att detta hinns med
* - Bryt ut alla URL-funktioner i egen modul
* - Bättre felhantering av felaktiga argument i kommandorad