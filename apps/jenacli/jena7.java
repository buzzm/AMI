
// The custom triple store!
import org.moschetti.jena.mongodb.core.* ;

import com.sun.net.httpserver.HttpServer;

import org.apache.jena.rdf.model.* ;

import org.apache.jena.query.* ;


import java.net.URI;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.Date;
import java.util.Map;
import java.util.HashMap;

import java.util.Scanner;

import java.io.ByteArrayOutputStream;
import java.io.ObjectOutputStream;
import java.io.ObjectOutput;
import java.io.File;


public class jena7 {

    public static void main(String[] args) {

	try {

	    String host = "mongodb://localhost:37017/?replicaSet=rs0";

	    JenaMongoConnection mc = new JenaMongoConnection(host);
	    JenaMongoStore ms = new JenaMongoStore(mc, "semantic");

	    // After this call, it's all Jena interfaces; no more triple store specifics!
	    Model mm = JenaMongoDataset.createModel(ms, args[0]);	    


	    Dataset ds = DatasetFactory.create(mm);

	    Scanner console = new Scanner(System.in);

	    String filename = args[1];

	    while(true) {
		System.out.print("ENTER to read " + filename + "> ");
		String cmd = console.nextLine();

		String queryString = new Scanner(new File(filename)).useDelimiter("\\Z").next();
		
		//System.out.println("exec:" + queryString);
		
		try {
		    Query query = QueryFactory.create(queryString);
		
		    // System.out.println("query: " + query);

		    try (QueryExecution qexec = QueryExecutionFactory.create(query, ds)) {

			//System.out.println("qexec: " + qexec);

			ResultSet results = qexec.execSelect() ;

			List<String> vars = results.getResultVars();
			System.out.println("vars:" + vars);

			int n = 0;
			for ( ; results.hasNext() ; )
			    {
				//QuerySolution soln = results.nextSolution() ; 
				QuerySolution soln = results.next() ;
				n++;
				System.out.println(results.getRowNumber() + " " + n);
				System.out.println(soln);
				processOneSolution(soln);
			    }
			System.out.printf("found %d\n", n);
		    }
		} catch(org.apache.jena.query.QueryParseException e) {
		    System.out.println("parse failure: " + e);		    
		} catch(Exception e) {
		    throw(e);
		}
	    }
		

	} catch(Exception e) {
	    System.out.println("epic fail: " + e);
	    e.printStackTrace();
	}
    }


    private static void XXprocessOneSolution(QuerySolution soln) {
	System.out.println(soln);
    }

    private static void pp(String varname, String type, String sval) {
	System.out.printf("  %-20s %8s %s\n", varname, type, sval);
    }
	
    private static void processOneSolution(QuerySolution soln) {
	java.util.Iterator<String> varNames = soln.varNames();
	while (varNames.hasNext()) {
	    String varName = varNames.next();
	    RDFNode node = soln.get(varName);

	    if(node == null) {
		pp(varName, "null", "");
	    } else {
		if (node.isURIResource()) {
		    Resource resource = node.asResource();
		    pp(varName, "URI", resource.getURI());
		} else if (node.isLiteral()) {
		    Literal literal = node.asLiteral();
		    pp(varName, "literal", literal.getDatatype() + ":" + literal.getString());
		} else if (node.isAnon()) {
		    Resource anonResource = node.asResource();
		    pp(varName, "blank", anonResource.getURI());
		} else if (node.isResource()) {
		    Resource resource = node.asResource();
		    pp(varName, "resource", resource.toString());
		} else {
		    pp(varName, "UNK", "");
		}
	    }
	}
    }
    
}
