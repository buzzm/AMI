#  python3 ttldump.py ami.ttl data2.ttl

import lightrdf
import pymongo

#import json
import bson

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
    # 1        1        2         3         4 2
    
    if '^^' in input_str:
        value_part, type_part = input_str.split('^^')
        
        # Extract the type after the hash and remove the trailing >
        type_part = type_part[34:-1]

        value = value_part + "^^xsd:" + type_part
            
        return value
    else:
        # (Optional...?  Do markdown interp of CR:
        value = groom(input_str.strip('"'))

        return '"' + value + '"'


def main():
    connstr = "mongodb://localhost:37017/semantic?replicaSet=rs0"
    
    parser = argparse.ArgumentParser(description=
"""Dump turtle RDF into format gpt-4-turbo can easily digest.
"""
   )
    parser.add_argument('--format',
                        metavar='nt,cpt',
                        default='cpt')
    
    parser.add_argument('RDF',
                        nargs='+')
                        
    rargs = parser.parse_args()


    fnames = rargs.RDF

    rdfp = lightrdf.Parser()



    #  Scan for prefixes!
    pfx = {}

    for f in fnames:
        with open(f,'r') as fd:
            for line in fd:
                if line[0:7] == '@prefix':
                    q = line.split(' ')
                    ns = q[2][1:-1] # get rid of leading and trailing < > 
                    pfx[ns] = q[1]

    # Underscore is special and maps birectionally to itself:
    pfx['_'] = '_'   # smiley!  LOL


    format = rargs.format
    
    for f in fnames:
        for triple in rdfp.parse(f, base_iri=None):
            z2 = []

            if format == 'cpt':
                for ns in triple:
                    if ns[0] == '<':
                        ns = ns[1:-1]
                    z2.append(substitute_namespace(pfx, ns))

                # Check for literal objects; lightrdf will wrap them with doublequotes
                if z2[2][0] == '"':
                    z2[2] = cvtString(z2[2])

                print(f'{z2[0]}|{z2[1]}|{z2[2]}')
            else:
                #  Watch for the dot terminator!
                print(f'{triple[0]} {triple[1]} {triple[2]} .')
                    
            
if __name__ == "__main__":        
    main()
        
