# Main fil för projektet.

import argparse
import validators

from integration import Integrator

#Funktionerna verifierar angivna argument.
def is_url(url):
    return validators.url(url)

def check_arguments_url(urls):
    for url in urls:
        if is_url(url) is False:
            return False
        
    return True

if __name__ == "__main__":

    #Hanterar kommandoradsargument.
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--urls", nargs="+", help="En eller flera URL:er att skanna", required=True)
    parser.add_argument("-a", "--apikey", help="ZAP API-nyckel", required=True)

    arguments = parser.parse_args()

    if check_arguments_url(arguments.urls):
        #Integrator ansvarar för hela processen.
        integrator = Integrator(arguments.urls, arguments.apikey)
        integrator.execute()
    else:
        print("Felaktiga argument, kräver -u med url:er samt -a med API-key.")