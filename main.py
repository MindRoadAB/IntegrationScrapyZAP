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

def check_mode_argument(mode):
    return True if mode == "classic" or mode == "ajax" or mode == "js" else False

if __name__ == "__main__":

    #Hanterar kommandoradsargument.
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--urls", nargs="+", help="En eller flera URL:er att skanna", required=True)
    parser.add_argument("-a", "--apikey", help="ZAP API-nyckel", required=True)
    parser.add_argument("-m", "--mode", help="Vilken crawlingmetod som används", required=False)

    arguments = parser.parse_args()

    if check_arguments_url(arguments.urls) and check_mode_argument(arguments.mode):
        integrator = Integrator(arguments.urls, arguments.apikey, arguments.mode)
        integrator.execute()
    else:
        print("Felaktiga argument angivna.")