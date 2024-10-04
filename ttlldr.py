#  python3 ttlldr.py  --drop ami.ttl data2.ttl

import lightrdf
import pymongo

#import json
import bson
from decimal import Decimal

import datetime
import argparse
import re
import sys

def substitute_namespace(namespaces, candidate):
    for key, value in namespaces.items():
        if candidate.startswith(key):
            return candidate.replace(key, value, 1)
    return candidate

def groom(text: str) -> str:
    # First, replace sequences of more than one '\n' with a newline character repeated as many times as there are '\n'
    text = re.sub(r'(\\n){2,}', lambda m: '\n' * (len(m.group(0)) // 2), text)
    
    # Then, replace any remaining single '\n' with a space
    text = text.replace(r'\n', ' ')
    
    # Finally, strip any leading or trailing spaces/newlines
    return text.strip()


def cvtString(input_str):
    # "bla"    string

    # "bla"^^<http://www.w3.org/2001/XMLSchema#integer>  cast to type beyond hash

    if '^^' in input_str:
        # Split the string at ^^
        value_part, type_part = input_str.split('^^')
        
        # Remove the quotes from the value part
        value = value_part.strip('"')
        
        # Extract the type after the hash and remove the trailing >
        type_identifier = type_part.split('#')[-1][:-1]

        if 'integer' == type_identifier:
            value = int(value)

        elif 'double' == type_identifier or 'float' == type_identifier:
            value = float(value)
            
        elif 'decimal' == type_identifier:
            xx = Decimal(value)
            value = bson.decimal128.Decimal128(xx)

        elif 'dateTime' == type_identifier:
            if value.endswith('Z'):
                value = value[:-1] + '+00:00'
            value = datetime.datetime.fromisoformat(value)

        elif 'json' == type_identifier:
            #  turtle needs to escape the double quotes like this:
            #     ami:corn "{\"key\": [\"foo\",12 ] }"^^ex:json  ;
            #  when the value comes out it will be
            #     {\"key\": [\"foo\",12 ] }
            #  so we must replace \" with ".

            #  Should probably wrap this with try/except; lots could go wrong:
            value = value.replace(r'\"', '"')
            
            #value = json.loads(value)
            value = bson.json_util.loads(value)            

        else:
            print("warning: literal [%s]; unknown cast type [%s]; assuming string value [%s]" % (input_str, type_identifier, value))
            
        return value
    else:
        # Remove the quotes from the input string
        value = input_str.strip('"')

        # (Optional...?  Do markdown interp of CR:
        value = groom(value)

        if ':' in value:
            value = '!' + value   # JenaMongodbIOSchemeMode1
            
        return value


def main():
    connstr = "mongodb://localhost:37017/semantic?replicaSet=rs0"
    
    parser = argparse.ArgumentParser(description=
"""Load turtle RDF into MongoDB AMI-style.
"""
   )

    parser.add_argument('--mongoconn', 
                        metavar='mongoDB_URI',
                        default=connstr)

    parser.add_argument('--coll',
                        metavar='collection name',
                        default='ami5')
    
    parser.add_argument('--drop',
                        action='store_true')

    parser.add_argument('--nodb',
                        help='process inputs but do not load DB',
                        action='store_true')    

    parser.add_argument('RDF',
                        nargs='+')
                        
    rargs = parser.parse_args()


    fnames = rargs.RDF

    rdfp = lightrdf.Parser()

    print("syntax checking input files...")
    for f in fnames:
        try:
            for t in rdfp.parse(f, base_iri=None):
                pass
        except Exception as e:
            print("error:", f, ":", e)
            return
    
    if rargs.nodb:
        print("nodb mode")
    else:
        print("connecting to",rargs.mongoconn,rargs.coll,"...")
        client = pymongo.MongoClient(rargs.mongoconn)
        db = client.get_default_database()
        coll = db[rargs.coll]
    
        if rargs.drop:
            print("dropping",rargs.coll) 
            coll.drop()

    #  Scan for prefixes!
    pfx = {}

    for f in fnames:
        with open(f,'r') as fd:
            for line in fd:
                if line[0:7] == '@prefix':
                    q = line.split(' ')
                    ns = q[2][1:-1] # get rid of leading and trailing < > 
                    pfx[ns] = q[1]

    if not rargs.nodb:    
        #  TBD TBD   Need options on what kind of mode to load but for
        #  now, hardcode mode 1.
        hdr = {
            '_id': 'SCHEME',
            'mode': 1,
            'desc': """Colon-prefixed quasi-URIs make for vastly easier querying.
Object strings that contain a colon should be interpreted as an URI unless the
first char is the exclamation point in which case the object is a true string literal
that happens to contain a colon.            
All other object types are native e.g. datetimes are ISODate type.""" ,           
            'prefixes': [],
            'S': '_',
            'P': '_',
            'O': '_'
        }

        for (k,v) in pfx.items():
            hdr['prefixes'].append({'pfx':v, 'uri':k})
        
        #print("PFX",hdr)

        coll.insert_one(hdr)

    # Underscore is special and maps birectionally to itself:
    pfx['_'] = '_'   # smiley!  LOL

    #  ('<http://example.com/schema#myService>', '<http://example.com/schema#listensFor>', '_:riog00000001')
    #  ('_:riog00000001', '<http://example.com/schema#mep2>', '_:riog00000003')

    for f in fnames:
        print(f,"...")
        for triple in rdfp.parse(f, base_iri=None):
            z2 = []
            for ns in triple:
                if ns[0] == '<':
                    ns = ns[1:-1]
                z2.append(substitute_namespace(pfx, ns))


            # Check for literal objects; lightrdf will wrap them with doublequotes
            if z2[2][0] == '"':
                z2[2] = cvtString(z2[2])
                
            if not rargs.nodb:                
                doc = {
                    'S':z2[0],
                    'P':z2[1],
                    'O':z2[2]
                }
                coll.insert_one(doc)


        

if __name__ == "__main__":        
    main()
        
