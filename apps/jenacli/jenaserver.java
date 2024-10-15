
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import org.apache.jena.query.*;
import org.apache.jena.rdf.model.*;

import org.moschetti.jena.mongodb.core.* ;

import org.json.JSONObject;
import org.json.JSONArray;

import java.io.*;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Iterator;

import java.util.Objects;
import java.util.Map;
import java.util.HashMap;

public class jenaserver {

    private static final Map<String, String> uriToPrefixMap = new HashMap<>();
    
    static {
	// Industry Standards:
        uriToPrefixMap.put("http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdf");
        uriToPrefixMap.put("http://www.w3.org/2000/01/rdf-schema#", "rdfs");
        uriToPrefixMap.put("http://www.w3.org/2001/XMLSchema#", "xsd");
        uriToPrefixMap.put("http://www.w3.org/ns/shacl#", "sh");

	// AMI Standards.  Should probably be driven by config...
        uriToPrefixMap.put("http://moschetti.org/ami#", "ami");

	// Internal AMI service...
	uriToPrefixMap.put("http://moschetti.org/buzz#", "dd");
        uriToPrefixMap.put("http://moschetti.org/compliance#", "exc");

	// External AMI service:
	uriToPrefixMap.put("http://http://xts.com/xts#", "xts");
    }
    
    private static Dataset ds;


    // usage:  jenaserver port targetCollection [ mongodb conn str ]
    
    public static void main(String[] args) {
        try {
            // Initialization part - MongoDB and Jena setup
            String host = "mongodb://localhost:37017/?replicaSet=rs0";

	    if(args.length == 3) {
		host = args[2];
	    }
	    System.out.println("\n\n**using " + host);
	    
            JenaMongoConnection mc = new JenaMongoConnection(host);
            JenaMongoStore ms = new JenaMongoStore(mc, "semantic");

            // Jena interfaces
            Model mm = JenaMongoDataset.createModel(ms, args[1]);           
            ds = DatasetFactory.create(mm);

            // HTTP Server setup
	    int port = Integer.parseInt(args[0]);
            HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
            server.createContext("/sparql", new QueryHandler());
            server.setExecutor(null); // Use the default executor
            System.out.println("Server is listening on port " + port);
            server.start();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

	
    private static void emit(OutputStream os, JSONObject obj)
	throws IOException
    {
	String t = obj.toString();			
	os.write(t.getBytes(StandardCharsets.UTF_8));
	os.write("\n".getBytes(StandardCharsets.UTF_8));	
    }

    public static String generatePfx() {
	StringBuilder sb = new StringBuilder();
	for (Map.Entry<String, String> entry : uriToPrefixMap.entrySet()) {
	    sb.append("PREFIX ").append(entry.getValue())
		.append(": <").append(entry.getKey()).append(">\n");
	}
	return sb.toString();
    }

    public static String substitutePrefix(String uri) {
	for (Map.Entry<String, String> entry : uriToPrefixMap.entrySet()) {
	    if (uri.startsWith(entry.getKey())) {
		return entry.getValue() + ":" + uri.substring(entry.getKey().length());
	    }
	}
	return "_:notFound"; // Return default if no match is found
    }
	
	
    
    // Handler class for processing HTTP requests
    static class QueryHandler implements HttpHandler {

	private final int NOT_FIXED_LENGTH = 0 ; // special val to indicate no Content-Length

	private final String pfx = generatePfx();

	
        @Override
	public void handle(HttpExchange exchange) throws IOException {
	    String requestMethod = exchange.getRequestMethod();

	    if ("POST".equals(requestMethod)) {
		// Handle POST request (query in request body)
		handlePOST(exchange);
	    } else if ("GET".equals(requestMethod)) {
		handleGET(exchange);
	    } else {
		// Handle non-GET and non-POST requests
		exchange.sendResponseHeaders(405, -1); // Method Not Allowed
	    }
	}
	
        private void handlePOST(HttpExchange exchange) throws IOException {
	    InputStreamReader isr = new InputStreamReader(exchange.getRequestBody(), StandardCharsets.UTF_8);
	    BufferedReader br = new BufferedReader(isr);
	    StringBuilder sb = new StringBuilder(pfx);
	    
	    char[] buffer = new char[4096]; // Read in chunks of 1024 characters
	    int bytesRead;
	    while ((bytesRead = br.read(buffer, 0, buffer.length)) != -1) {
		sb.append(buffer, 0, bytesRead);  // Append the read chunk to the StringBuilder
	    }
	    String queryString = sb.toString();
	    processSparqlQuery(exchange, queryString);
	}

	private void handleGET(HttpExchange exchange) throws IOException {
	    // Extract the query parameter from the URL
	    URI requestURI = exchange.getRequestURI();
	    String queryParam = getQueryParameter(requestURI.getQuery(), "query");

	    //application/sparql-results+json

	    if (queryParam != null) {
		// Process the SPARQL query
		//System.out.println("GOT: " + queryParam);

		//  TBD TBD   Assume for moment GET reqs will be SPARQL 1.1
		//  JSON response compliant
		handleStdSparql(exchange, queryParam);

	    } else {
		// Respond with 400 Bad Request if the query parameter is missing
		exchange.sendResponseHeaders(400, -1); // Bad Request
	    }
	}
	
	private String getQueryParameter(String query, String key) {
	    if (query == null || key == null) return null;
	    
	    String[] pairs = query.split("&");
	    for (String pair : pairs) {
		String[] param = pair.split("=");
		if (param.length == 2 && param[0].equals(key)) {
		    return param[1]; // Return the query parameter value
		}
	    }
	    return null; // Return null if not found
	}

	
	private void processSparqlQuery(HttpExchange exchange, String queryString)
	    throws IOException
	{	
	    JSONObject jsonResponse = new JSONObject();
		    
	    // Execute SPARQL query (you might adjust the query based on `question`)
	    
	    try {
		Query query = QueryFactory.create(queryString);
		
		try (QueryExecution qexec = QueryExecutionFactory.create(query, ds)) {
		    ResultSet results = qexec.execSelect();
		    List<String> vars = results.getResultVars();
		    
		    // If you got here, it worked.
		    // There might be zero rows, but the query exec'd OK.
		    exchange.sendResponseHeaders(200, NOT_FIXED_LENGTH);
		    
		    OutputStream os = exchange.getResponseBody();
		    
		    // Prepare the JSON response
		    JSONArray varsArray = new JSONArray(vars);
		    jsonResponse.put("status", "OK");
		    jsonResponse.put("vars", varsArray);
		    emit(os, jsonResponse);
		    
		    while (results.hasNext()) {
			QuerySolution soln = results.next();
			processOneSolution(soln, os);
		    }
		    
		    os.close();			
		}
		
	    } catch (org.apache.jena.query.QueryParseException e) {
		System.out.println("Parse exception");
		System.out.printf("INPUT [%s]\n", queryString);
		System.out.println("Exception: " + e);
		
		String msg = e.getMessage();
		int col = e.getColumn();
		int line = e.getLine();
		
		jsonResponse.put("status", "FAIL");
		jsonResponse.put("category", "parse");
		
		jsonResponse.put("msg", msg);
		jsonResponse.put("col", col);
		jsonResponse.put("line", line);
		
		exchange.sendResponseHeaders(400, NOT_FIXED_LENGTH);
		OutputStream os = exchange.getResponseBody();
		emit(os, jsonResponse);		    
		os.close();					       
		
	    } catch (Exception e) {
		System.out.println("General Jena failure; continuing..."  + e);
		jsonResponse.put("status", "FAIL");
		jsonResponse.put("category", "general");		    
		jsonResponse.put("msg", e.toString());
		
		exchange.sendResponseHeaders(400, NOT_FIXED_LENGTH);
		OutputStream os = exchange.getResponseBody();
		
		emit(os, jsonResponse);		    
		os.close();					    
	    }
        }
    }

    // Process a single SPARQL query solution
    private static void processOneSolution(QuerySolution soln, OutputStream os)
	throws IOException
    {
	JSONObject row = new JSONObject();

        Iterator<String> varNames = soln.varNames();
        while (varNames.hasNext()) {
            String varName = varNames.next();
            RDFNode node = soln.get(varName);
			
            if (node.isURIResource()) {
		String uri = node.asResource().getURI();
		String pfx = substitutePrefix(uri);
		row.put(varName, pfx);

            } else if (node.isLiteral()) {
		row.put(varName, node.asLiteral().getString());
            } else if (node.isAnon()) {
                //sparqlResults.append(varName).append(": blank node\n");
            } else {
                //sparqlResults.append(varName).append(": unknown type\n");
            }
        }
	emit(os, row);	    
    }


    public static void handleStdSparql(HttpExchange exchange, String queryString)
	throws IOException 
    {
	Query query = QueryFactory.create(queryString);

        try (QueryExecution qexec = QueryExecutionFactory.create(query, ds)) {
            ResultSet results = qexec.execSelect();
            List<String> vars = results.getResultVars();

            // Build the JSON response object
            JSONObject jsonResponse = new JSONObject();

            // "head" section with variable names
            JSONObject head = new JSONObject();
            JSONArray varsArray = new JSONArray(vars);
            head.put("vars", varsArray);
            jsonResponse.put("head", head);

            // "results" section with bindings
            JSONObject resultsObj = new JSONObject();
            JSONArray bindingsArray = new JSONArray();

            // Prepare the JSON response for all solutions
            while (results.hasNext()) {
                QuerySolution soln = results.next();
                JSONObject binding = processStdSparqlSolution(soln, vars);
                bindingsArray.put(binding);
            }

            resultsObj.put("bindings", bindingsArray);
            jsonResponse.put("results", resultsObj);

	    // Very important!
	    exchange.getResponseHeaders().set("Content-Type", "application/sparql-results+json");
	    
            // Send the HTTP response
            exchange.sendResponseHeaders(200, jsonResponse.toString().length());
            OutputStream os = exchange.getResponseBody();
            os.write(jsonResponse.toString().getBytes(StandardCharsets.UTF_8));
            os.close();
        }
    }

    private static JSONObject processStdSparqlSolution(QuerySolution soln, List<String> vars) {
        JSONObject binding = new JSONObject();

        // Iterate over all variables
        for (String varName : vars) {
            RDFNode node = soln.get(varName);

            if (node != null) {
                JSONObject valueObj = new JSONObject();

                if (node.isURIResource()) {
                    valueObj.put("type", "uri");
                    valueObj.put("value", node.asResource().getURI());

                } else if (node.isLiteral()) {
                    valueObj.put("type", "literal");
                    valueObj.put("value", node.asLiteral().getString());

                    // Optional: If you need datatype or language information
                    if (node.asLiteral().getDatatypeURI() != null) {
                        valueObj.put("datatype", node.asLiteral().getDatatypeURI());
                    } else if (node.asLiteral().getLanguage() != null && !node.asLiteral().getLanguage().isEmpty()) {
                        valueObj.put("xml:lang", node.asLiteral().getLanguage());
                    }

                } else if (node.isAnon()) {
                    valueObj.put("type", "bnode");
                    valueObj.put("value", node.asResource().getId().getLabelString());
                }

                // Add to the binding for the current variable
                binding.put(varName, valueObj);
            }
        }
        return binding;
    }
}

