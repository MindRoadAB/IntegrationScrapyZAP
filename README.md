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
* Bryta ut ZAP-funktioner i egen klass - UNDER ARBETE
* Lägga in funktionalitet för att dubbelkolla så inga felaktiga URL:er kommer tillbaka från crawler - UNDER ARBETE
* Lägga till flagga -m --mode för att kunna välja vilken sorts crawling som ska utföras - UNDER ARBETE
* Lägga till parsning och extraktion av mer än bara forms - UNDER ARBETE
* Lägga till AJAX-hantering - UNDER ARBETE