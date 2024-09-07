
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

public class jenaserver {

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
	
    // Handler class for processing HTTP requests
    static class QueryHandler implements HttpHandler {

	private int NOT_FIXED_LENGTH = 0 ; // special val to indicate no Content-Length

	private String pfx = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

PREFIX sh: <http://www.w3.org/ns/shacl#>

# ami is the model, buzz is "my data"
# Make sure the ami5 collection _id = SCHEME has a prefixes entry
# that matches these!
PREFIX ami: <http://moschetti.org/ami#>
PREFIX ex: <http://moschetti.org/buzz#>
PREFIX exc: <http://moschetti.org/compliance#>
	    
	    """;
	
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
		
                // Execute SPARQL query (you might adjust the query based on `question`)

                try {
                    Query query = QueryFactory.create(queryString);

                    try (QueryExecution qexec = QueryExecutionFactory.create(query, ds)) {
			JSONObject jsonResponse = new JSONObject();
                        ResultSet results = qexec.execSelect();
                        List<String> vars = results.getResultVars();

			// If you got here, it worked.
			exchange.sendResponseHeaders(200, NOT_FIXED_LENGTH);

			OutputStream os = exchange.getResponseBody();
		
                        // Prepare the JSON response
                        JSONArray varsArray = new JSONArray(vars);
                        jsonResponse.put("vars", varsArray);
			emit(os, jsonResponse);
			
                        while (results.hasNext()) {
                            QuerySolution soln = results.next();
                            processOneSolution(soln, os);
                        }

			os.close();			
                    }
                } catch (Exception e) {
                    System.out.println("Query execution failed; continuing...");
		    exchange.sendResponseHeaders(400, NOT_FIXED_LENGTH);
		    OutputStream os = exchange.getResponseBody();
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
		row.put(varName, node.asResource().getURI());
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

