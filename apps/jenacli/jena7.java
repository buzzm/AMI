
import org.moschetti.jena.mongodb.core.* ;


// The Model
import org.apache.jena.rdf.model.* ;

import org.apache.jena.query.* ;

import org.apache.jena.iri.*;

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

    // usage:   sh jena.runt jena7 collection sparqlfile
    // example: sh jena.runt jena7 elm3 sparql3.spq

    public static void main(String[] args) {

	try {

	    IRIFactory iriFactory = IRIFactory.jenaImplementation();

	    URI uri = URI.create("http://moschetti.org/foo/bar");
	    IRI iri = iriFactory.create(uri);	

	    System.out.println("iri: " + iri);


	    
	    String host = "mongodb://localhost:37017/?replicaSet=rs0";

	    JenaMongoConnection mc = new JenaMongoConnection(host);
	    JenaMongoStore ms = new JenaMongoStore(mc, "semantic");

	    Model mm = JenaMongoDataset.createRDFSModel(ms, args[0]);

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
			int n = 0;
			for ( ; results.hasNext() ; )
			    {
				QuerySolution soln = results.nextSolution() ;
				System.out.println(soln);
				n++;
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


}
