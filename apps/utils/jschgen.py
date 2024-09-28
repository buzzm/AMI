import rdflib
import json

from rdflib.namespace import RDF, RDFS, XSD
import random
import datetime

class Faker():
    def __init__(self):
        pass

    def date_time(self):
        return datetime.datetime.utcnow()

    def email(self):
        return "corn@dog.com"

    def word(self):
        return "corn"    

faker = Faker()

# Namespaces
SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
EX = rdflib.Namespace("http://example.org/ex#")

def parse_rdf_file(rdf_file):
    g = rdflib.Graph()
    g.parse(rdf_file, format="turtle")
    return g

def get_top_level_shape(graph, target_shape):
    # Extract the shape by IRI
    shape = rdflib.URIRef(target_shape)
    if (shape, RDF.type, SH.NodeShape) in graph:
        return shape
    else:
        raise ValueError(f"Shape {target_shape} not found in the graph.")

def shacl_to_jsonschema(graph, shape):
    schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    # Process SHACL properties
    for prop in graph.objects(shape, SH.property):
        path = graph.value(prop, SH.path)
        datatype = graph.value(prop, SH.datatype)
        node = graph.value(prop, SH.node)
        comment = graph.value(prop, RDFS.comment)

        property_name = path.split("#")[-1] if isinstance(path, rdflib.URIRef) else str(path)

        # Handle nested node shapes recursively
        if node:
            schema["properties"][property_name] = shacl_to_jsonschema(graph, node)
        else:
            # Handle datatype mapping
            schema["properties"][property_name] = map_shacl_datatype_to_jsonschema(datatype)
            if comment is not None:
                schema["properties"][property_name]['description'] = comment
                
            schema["required"].append(property_name)

    
    return schema

def map_shacl_datatype_to_jsonschema(datatype):
    if datatype == XSD.string:
        return {"type": "string"}
    elif datatype == XSD.integer:
        return {"type": "integer"}
    elif datatype == XSD.dateTime:
        return {"type": "string", "format": "date-time"}
    else:
        return {"type": "string"}  # Default to string if unknown

def generate_mock_data(json_schema):
    mock_data = {}
    
    for prop, details in json_schema['properties'].items():
        if details["type"] == "string":
            if "format" in details and details["format"] == "date-time":
                mock_data[prop] = faker.date_time().isoformat()
            elif "pattern" in details:
                mock_data[prop] = faker.email() if "@" in details["pattern"] else faker.phone_number()
            else:
                mock_data[prop] = faker.word()
        elif details["type"] == "integer":
            mock_data[prop] = random.randint(1, 100)
        elif details["type"] == "object":
            # Recursively generate data for nested objects
            mock_data[prop] = generate_mock_data(details)
    
    return mock_data


def main(rdf_file, target_shape, generate_sample=False):
    # Step 1: Parse the RDF file
    graph = parse_rdf_file(rdf_file)
    
    # Step 2: Get the top-level shape
    shape = get_top_level_shape(graph, target_shape)
    
    # Step 3: Convert SHACL to JSON Schema
    json_schema = shacl_to_jsonschema(graph, shape)
    
    # Output the JSON schema
    print(json.dumps(json_schema, indent=4))
    
    # Step 4: Optionally generate a mocked sample instance
    if generate_sample:
        mock_instance = generate_mock_data(json_schema)
        print("Sample instance:")
        print(json.dumps(mock_instance, indent=4))

# Example usage
rdf_file = "qqq.ttl"  # File containing RDF shapes
target_shape = "http://moschetti.org/buzz#myShape_001"  # Target shape IRI

main(rdf_file, target_shape, generate_sample=True)

