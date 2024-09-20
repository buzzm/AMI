
// The custom triple store!
import org.moschetti.jena.mongodb.core.* ;

import com.sun.net.httpserver.HttpServer;

import org.apache.jena.rdf.model.* ;

//import org.apache.jena.query.* ;

import org.apache.jena.query.Query;
import org.apache.jena.query.QueryFactory;
import org.apache.jena.query.QuerySolution;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.Dataset;
import org.apache.jena.query.DatasetFactory;
import org.apache.jena.query.ResultSet;


import org.apache.jena.sparql.algebra.Algebra;
import org.apache.jena.sparql.algebra.Op;
import org.apache.jena.sparql.algebra.OpVisitorBase;
import org.apache.jena.sparql.algebra.op.OpFilter;
import org.apache.jena.sparql.algebra.op.OpGroup;
import org.apache.jena.sparql.algebra.op.OpProject;
//import org.apache.jena.sparql.algebra.walker.OpWalker;
import org.apache.jena.sparql.algebra.OpWalker;


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

    /* usage:  jena7 triple_collection filename [ mongo connstr ]  */
    
    public static void main(String[] args) {

	try {
	    String host = "mongodb://localhost:37017/?replicaSet=rs0";
	    if(args.length == 3) {
		host = args[2];
	    }
	    System.out.println("\n\n**using " + host);
		    
	    
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


		    analyze(query);

		    
		    // System.out.println("query: " + query);
		    System.out.println("AAAA");
			
		    try (QueryExecution qexec = QueryExecutionFactory.create(query, ds)) {

			System.out.println("BBBB qexec: " + qexec);

			// Nothing happens until execSelect() is called.
			// Then the underlying graph/find/mongodb machinery is invoked.
			ResultSet results = qexec.execSelect() ;

			System.out.println("CCCC");

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

    private static void analyze(Query query) {
	Op algebra = Algebra.compile(query);

	// Use OpWalker to traverse the algebra and identify optimization points
	OpWalker.walk(algebra, new OpVisitorBase() {
		@Override
		public void visit(OpFilter opFilter) {
		    // Inspect filter conditions for pushdown to MongoDB
		    System.out.println("Found filter: " + opFilter.getExprs());
		}
		
		@Override
		public void visit(OpGroup opGroup) {
		    // Identify aggregation opportunities
		    System.out.println("Found aggregation: " + opGroup.getAggregators());
		}
		
		@Override
		public void visit(OpProject opProject) {
		    // Optimize projections
		    System.out.println("Found projection: " + opProject.getVars());
		}
	    });
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
