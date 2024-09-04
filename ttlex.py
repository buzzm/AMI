from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import XSD

# Define namespaces
AMI = Namespace("http://moschetti.org/ami#")
EX = Namespace("http://example.org/ex/")

# Initialize the graph and bind namespaces
g = Graph()
g.bind("ami", AMI)
g.bind("ex", EX)

# Define the Turtle data
turtle_data = """

@prefix ami: <http://moschetti.org/ami#> .
@prefix ex: <http://example.org/ex/> .

ex:software2 a ami:Software;
    ami:basename "java";
    ami:vendor ex:actor4 ;
    ami:version [ a ami:Version; ami:major 8; ami:minor 2; ami:patch 3 ];
    ami:EOL "2025-01-01T00:00:00Z"^^<http://www.w3.org/2001/XMLSchema#dateTime> ;
    ami:steward ex:actor1 ;
    ami:linksWith ex:software7 , ex:software8 .
"""

ami_data_f = "/Users/buzz/git/AMI/data.ttl"
with open(ami_data_f) as fd:
    turtle_data = fd.read()    


# Parse the input Turtle data
g.parse(data=turtle_data, format="turtle")

# Define the new properties and values
new_properties = {
    "owner": EX.actor6,
    "steward": EX.actor9,
    "created": Literal("2022-01-01T00:00:00Z", datatype=XSD.dateTime),
    "createdBy": EX.actorSys
}

# Iterate over all top-level subjects in the graph (those that are not objects)
n = 0
for subject in g.subjects():
    if isinstance(subject, URIRef):  # Consider only top-level entities
        for prop, value in new_properties.items():
            property_uri = AMI[prop]
            if (subject, property_uri, None) not in g:
                g.add((subject, property_uri, value))

                
# Serialize the graph back into Turtle format, using only the "ami" prefix
output_data = g.serialize(format="turtle", prefix="ami", namespace_manager=g.namespace_manager)

print(output_data)
