import requests
import json

#  LOL!!!!

def fetch(name):
    url = 'https://endoflife.date/api/' + name + '.json'

    response = requests.get(url)

    qq = response.json()
    return qq

def process(name):
    qq = fetch(name)

    # qq is an array of cycles and such for the name.
    # Write each as JSON, CR-delimited style:
    for dd in qq:
        dd['name'] = name
        print(json.dumps(dd))
    
def main():
    #  LOL!  'all' is a special product; it gives the whole list!
    big_list = fetch('all')

    n = -1
    for name in big_list:
        if 0 == n:
            break
        process(name)
        n -= 1

    #print("process",n,"items")
    
if __name__ == "__main__":        
    main()
    
