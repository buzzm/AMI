import argparse
from rdflib import Graph, URIRef, BNode, Namespace
from rdflib import Literal, XSD

from rdflib.namespace import RDF

def format_literal(o):
    """Format literals properly, emitting numbers without quotes and escaping strings."""
    if isinstance(o, Literal):
        # If the literal has a numeric datatype, emit it without quotes
        if o.datatype in {XSD.integer, XSD.decimal, XSD.float, XSD.double}:
            return o.value  # Emit the raw value (e.g., 2, 3.14, etc.)

        # Otherwise, if it's a string, escape backslashes and wrap it in quotes
        elif o.datatype is None or o.datatype == XSD.string or o.language is not None:
            escaped_value = str(o).replace("\\", "\\\\")  # Escape backslashes
            if '\n' in escaped_value:
                return f'"""{escaped_value}"""'
            else:
                return f'"{escaped_value}"'                
        else:
            # For other datatypes (e.g., dateTime), include the datatype
            return f'"{o}"^^<{o.datatype}>'

    # If it's not a literal, handle as before
    return graph.namespace_manager.normalizeUri(o)

# Function to recursively generate Turtle output with indentation
def turtle_recursive(graph, subject, depth=0):
    indentation = "    " * (depth+1)
    output = []

    # Find all triples where the subject is the current subject (could be URI or blank node)
    for s, p, o in graph.triples((subject, None, None)):
        # Get the prefix version or fallback to full URI
        pred = graph.namespace_manager.normalizeUri(p)

        # If the object is a blank node, recurse into it
        if isinstance(o, BNode):
            output.append(f"{indentation}{pred} [")
            output.extend(turtle_recursive(graph, o, depth + 1))
            output.append(f"{indentation}] ;")
        # If the object is a literal or URI, print it directly
        else:
            obj = graph.namespace_manager.normalizeUri(o) if isinstance(o, URIRef) else format_literal(o)
            output.append(f"{indentation}{pred} {obj} ;")

    # Clean up the last semicolon but ONLY at very end!
    if depth == 0 and output and output[-1].endswith(';'):
        output[-1] = output[-1][:-2] + " ."

    return output

# Function to initiate Turtle reconstruction
def reconstruct_turtle(graph, target_shape):
    output = [f"{graph.namespace_manager.normalizeUri(target_shape)} a sh:NodeShape, ami:Shape ;"]
    
    output.extend(turtle_recursive(graph, target_shape, 0))
    return "\n".join(output)


def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="""
Read a file in N-triple format and convert it to Turtle format.
N-triple is the full blown bulky representation:  URI URI URI|literal .
<http://moschetti.org/buzz#myShape_002> <http://moschetti.org/ami#steward> <http://moschetti.org/buzz#actor7> .
<http://moschetti.org/buzz#myShape_002> <http://moschetti.org/ami#owner> <http://moschetti.org/buzz#actor7> .
<http://moschetti.org/buzz#myShape_002> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://moschetti.org/ami#Shape> .
    """)

    # Add the required positional arguments: filename and shapename
    parser.add_argument('filename', type=str, help='The name of the n-triple file to process')
    parser.add_argument('shapename', type=str, help='The shape to be converted')

    # Add an optional boolean argument: --force
    #parser.add_argument('--force', action='store_true', help='Force the operation even if it is not safe')

    args = parser.parse_args()

    # Load the graph and parse N-Triples
    g = Graph()

    #  TBD TBD
    g.namespace_manager.bind("ami", Namespace("http://moschetti.org/ami#"))
    g.namespace_manager.bind("ex", Namespace("http://moschetti.org/buzz#"))

    g.parse(args.filename, format="ntriples")

    target_shape_uri = URIRef(args.shapename)
        
    # Check for existend 
    def shapeExists(target_shape_uri):
        for s, p, o in g.triples((target_shape_uri, None, None)):
            return True  # got at least 1!
        return False
    
    if False == shapeExists(target_shape_uri):
        print("error: no such shape in n-triple file")
        return
        
    for prefix, namespace in list(g.namespace_manager.namespaces()):
        print(f"@prefix {prefix}: <{namespace}> .")    

    turtle_output = reconstruct_turtle(g, target_shape_uri)

    print(turtle_output)

if __name__ == "__main__":        
    main()
        
    
