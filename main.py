# Main fil för projektet.

import argparse
import validators

from integration import Integrator

#Funktionerna verifierar angivna argument.
def is_url(url):
    return validators.url(url)

def check_arguments(urls):
    for url in urls:
        if is_url(url) is False:
            return False
        
    return True

if __name__ == "__main__":

    #Hanterar kommandoradsargument.
    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs='+')
    arguments = parser.parse_args()

    if check_arguments(arguments.url):
        #Integrator ansvarar för hela processen.
        integrator = Integrator(arguments.url)
        integrator.execute()
    else:
        print("Invalid argument present, not an URL.")