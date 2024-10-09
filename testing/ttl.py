import rdflib

graph = rdflib.Graph()
graph.parse("tests.ttl", format="ttl")

for s, p, o in graph.triples((None, None, None)):
    print(s,p,o,".")

