import requests
import json
import pymongo

from datetime import datetime



#  LOL!!!!

def cvtDate(name, candidate):
    ret = candidate

    if candidate is True or candidate is False:
        return ret  # quick bool check

    try:
        ret = datetime.strptime(candidate, '%Y-%m-%d')
    except:
        # not a date; probably a bad string...?
        print("name", name, "field", candidate, "is not YYYY-MM-DD")
        ret = None
        
    return ret

def process(coll, dd):
    #  Groom the data:
    for f in ['releaseDate','eol','latestReleaseDate']:
        if f in dd:
            dd[f] = cvtDate(dd['name'], dd[f])

    coll.insert_one(dd)

    
def main():
    connstr = "mongodb://localhost:37017/semantic?replicaSet=rs0"

    print("connecting to",connstr)
    client = pymongo.MongoClient(connstr)
    db = client.get_default_database()
    coll = db['eol']

    n = 0
    fd = open("z.json","r")
    for line in fd:
        dd = json.loads(line)
        process(coll, dd)
        n += 1
        if 0 == n % 1000:
            print(n,"...")
            
    print("loaded",n,"items")

    
if __name__ == "__main__":        
    main()
    
