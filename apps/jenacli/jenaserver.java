
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
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Iterator;

import java.util.Map;
import java.util.HashMap;

public class jenaserver {

    private static final Map<String, String> uriToPrefixMap = new HashMap<>();
    
    static {
        uriToPrefixMap.put("http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdf");
        uriToPrefixMap.put("http://www.w3.org/2000/01/rdf-schema#", "rdfs");
        uriToPrefixMap.put("http://www.w3.org/2001/XMLSchema#", "xsd");
        uriToPrefixMap.put("http://www.w3.org/ns/shacl#", "sh");
        uriToPrefixMap.put("http://moschetti.org/ami#", "ami");

	// Should probably be driven by config...
	uriToPrefixMap.put("http://moschetti.org/buzz#", "ex");
        uriToPrefixMap.put("http://moschetti.org/compliance#", "exc");	
    }
    
    private static Dataset ds;

    public static void main(String[] args) {
        try {
            // Initialization part - MongoDB and Jena setup
            String host = "mongodb://localhost:37017/?replicaSet=rs0";
            JenaMongoConnection mc = new JenaMongoConnection(host);
            JenaMongoStore ms = new JenaMongoStore(mc, "semantic");

            // Jena interfaces
            Model mm = JenaMongoDataset.createModel(ms, args[0]);           
            ds = DatasetFactory.create(mm);

            // HTTP Server setup
            HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
            server.createContext("/query", new QueryHandler());
            server.setExecutor(null); // Use the default executor
            System.out.println("Server is listening on port 8080...");
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
            if ("POST".equals(exchange.getRequestMethod())) {
                // Reading the input JSON
                InputStreamReader isr = new InputStreamReader(exchange.getRequestBody(), StandardCharsets.UTF_8);
                BufferedReader br = new BufferedReader(isr);
                StringBuilder sb = new StringBuilder(pfx);

                /*
		  String line;
                while ((line = br.readLine()) != null) {
		    System.out.println("LINE:" + line);
                    sb.append(line);
                }
		*/
		
		char[] buffer = new char[4096]; // Read in chunks of 1024 characters
		int bytesRead;
		while ((bytesRead = br.read(buffer, 0, buffer.length)) != -1) {
		    sb.append(buffer, 0, bytesRead);  // Append the read chunk to the StringBuilder
		}

                //String requestBody = sb.toString();
                // Parse the incoming JSON request
                //JSONObject jsonRequest = new JSONObject(requestBody);
                //String queryString = jsonRequest.getString("query");

                String queryString = sb.toString();

		JSONObject jsonResponse = new JSONObject();
		    
                // Execute SPARQL query (you might adjust the query based on `question`)

                try {
                    Query query = QueryFactory.create(queryString);

                    try (QueryExecution qexec = QueryExecutionFactory.create(query, ds)) {
                        ResultSet results = qexec.execSelect();
                        List<String> vars = results.getResultVars();

			// If you got here, it worked.
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
		    
                } catch (Exception e) {
                    System.out.println("Query execution failed; continuing..."  + e);
		    
		    exchange.sendResponseHeaders(400, NOT_FIXED_LENGTH);
		    OutputStream os = exchange.getResponseBody();
		    jsonResponse.put("status", "FAIL");
		    jsonResponse.put("msg", "query failed");
		    emit(os, jsonResponse);		    
		    os.close();					    
                }

            } else {
                // Handle non-POST requests
                exchange.sendResponseHeaders(405, -1); // Method Not Allowed
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
}

