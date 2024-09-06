
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

    // Handler class for processing HTTP requests
    static class QueryHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if ("POST".equals(exchange.getRequestMethod())) {
                // Reading the input JSON
                InputStreamReader isr = new InputStreamReader(exchange.getRequestBody(), StandardCharsets.UTF_8);
                BufferedReader br = new BufferedReader(isr);
                StringBuilder sb = new StringBuilder();

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
                JSONObject jsonResponse = new JSONObject();
                try {
                    Query query = QueryFactory.create(queryString);

                    try (QueryExecution qexec = QueryExecutionFactory.create(query, ds)) {
                        ResultSet results = qexec.execSelect();
                        List<String> vars = results.getResultVars();

                        // Prepare the JSON response
                        JSONArray varsArray = new JSONArray(vars);
                        jsonResponse.put("vars", varsArray);

                        StringBuilder sparqlResults = new StringBuilder();
                        while (results.hasNext()) {
                            QuerySolution soln = results.next();
                            processOneSolution(soln, sparqlResults);
                        }

                        jsonResponse.put("data", sparqlResults.toString());			
                    }
                } catch (Exception e) {
                    jsonResponse.put("error", "Query execution failed: " + e.getMessage());
                }

                // Send the JSON response
                String responseText = jsonResponse.toString();

		System.out.println("RESPONSE:" + responseText);
		
		
                exchange.sendResponseHeaders(200, responseText.length());
                OutputStream os = exchange.getResponseBody();
                os.write(responseText.getBytes(StandardCharsets.UTF_8));
                os.close();
            } else {
                // Handle non-POST requests
                exchange.sendResponseHeaders(405, -1); // Method Not Allowed
            }
        }
    }

    // Process a single SPARQL query solution
    private static void processOneSolution(QuerySolution soln, StringBuilder sparqlResults) {
        Iterator<String> varNames = soln.varNames();
        while (varNames.hasNext()) {
            String varName = varNames.next();
            RDFNode node = soln.get(varName);

            if (node.isURIResource()) {
                sparqlResults.append(varName).append(": URI ").append(node.asResource().getURI()).append("\n");
            } else if (node.isLiteral()) {
                sparqlResults.append(varName).append(": literal ").append(node.asLiteral().getString()).append("\n");
            } else if (node.isAnon()) {
                sparqlResults.append(varName).append(": blank node\n");
            } else {
                sparqlResults.append(varName).append(": unknown type\n");
            }
        }
    }
}

