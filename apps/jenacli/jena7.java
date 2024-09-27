
// The custom triple store!
import org.moschetti.jena.mongodb.core.* ;

import com.sun.net.httpserver.HttpServer;

import org.apache.jena.rdf.model.* ;

//import org.apache.jena.query.* ;
import org.apache.jena.graph.Node;
import org.apache.jena.graph.Triple;

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
import org.apache.jena.sparql.algebra.OpWalker;

import org.apache.jena.sparql.algebra.op.*;
/*import org.apache.jena.sparql.algebra.op.OpTriple;
import org.apache.jena.sparql.algebra.op.OpFilter;
import org.apache.jena.sparql.algebra.op.OpGroup;
import org.apache.jena.sparql.algebra.op.OpProject;
//import org.apache.jena.sparql.algebra.walker.OpWalker;
*/


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


		    //analyze(query);

		    
		    // System.out.println("query: " + query);
		    try (QueryExecution qexec = QueryExecutionFactory.create(query, ds)) {
			// Nothing happens until execSelect() is called.
			// Then the underlying graph/find/mongodb machinery is invoked.
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

    private static void analyze(Query query) {
	Op algebra = Algebra.compile(query);

	List sv = new ArrayList();
	List sc = new ArrayList();
	
	OpWalker.walk(algebra, new OpVisitorBase() {
		@Override
		public void visit(OpFilter opFilter) {
		    System.out.println("Found filter: " + opFilter.getExprs());
		}

		// Visit basic graph patterns (BGPs), which might contain multiple triples
		@Override
		public void visit(OpBGP opBGP) {
		    System.out.println("Visiting OpBGP");		    

		    for (Triple triple : opBGP.getPattern().getList()) {
			Node subject = triple.getSubject();
			Node predicate = triple.getPredicate();
			Node object = triple.getObject();

			if (subject.isVariable()) {
			    System.out.println("Subject variable: " + subject);
			} else {
			    System.out.println("Subject constant: " + subject);
			}

			if (predicate.isVariable()) {
			    System.out.println("Predicate variable: " + predicate);
			} else {
			    System.out.println("Predicate constant: " + predicate);
			}

			if (object.isVariable()) {
			    System.out.println("Object variable: " + object);
			} else {
			    System.out.println("Object constant: " + object);
			}
		    }
		}

		// Optionally, handle other operations like joins or sequences
		@Override
		public void visit(OpJoin opJoin) {
		    System.out.println("Visiting join operation");
		    opJoin.getLeft().visit(this);
		    opJoin.getRight().visit(this);
		}

		@Override
		public void visit(OpSequence opSequence) {
		    System.out.println("Visiting sequence operation");
		    for (Op op : opSequence.getElements()) {
			op.visit(this);
		    }
		}

		@Override
		public void visit(OpUnion opUnion) {
		    System.out.println("Visiting union operation");
		    opUnion.getLeft().visit(this);
		    opUnion.getRight().visit(this);
		}

		// Direct handling of individual triples, in case they're not part of a BGP
		@Override
		public void visit(OpTriple opTriple) {
		    Triple triple = opTriple.getTriple();
		    Node subject = triple.getSubject();
		    Node predicate = triple.getPredicate();
		    Node object = triple.getObject();

		    if (subject.isVariable()) {
			System.out.println("Subject variable: " + subject);
		    }
		    if (predicate.isVariable()) {
			System.out.println("Predicate variable: " + predicate);
		    }
		    if (object.isVariable()) {
			System.out.println("Object variable: " + object);
		    }
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
