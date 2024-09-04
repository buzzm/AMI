/**

The Persistor Experiment

 */

// The SPARQ engine that consumes the model
import org.moschetti.jena.mongodb.core.* ;

import org.apache.jena.query.* ;
import org.apache.jena.rdf.model.* ;
import org.apache.jena.rdf.model.impl.PropertyImpl;

public class jena4 {

    public static final String rdf_uri = "http://www.w3.org/1999/02/22-rdf-syntax-ns#";
    public static final String rdfs_uri="http://www.w3.org/2000/01/rdf-schema#";

    public static final String pfx = "a:";


    public static String makeResource(String val) {
	if(-1 == val.indexOf(":")) {
	    return pfx + val;
	} else {
	    String[] parts = val.split(":");
	    if(parts[0].equals("rdf")) {
		return rdf_uri + parts[1];
	    } else if(parts[0].equals("rdfs")) {
		return rdfs_uri + parts[1];
	    } else {
		//return val;
		return pfx + val; // OK for multiple :", e.g. a:Person:type
	    }
	}
    }

    private static void add(Model m, String s, String p, String o) {
	m.add(ResourceFactory.createStatement(
			  new PropertyImpl(makeResource(s)),
			  new PropertyImpl(makeResource(p)),
			  new PropertyImpl(makeResource(o)))
		  );
    }

    public void go(String[] args) {

	StringBuffer sb = new StringBuffer();
	
	//sb.append("PREFIX x: <x:>");
	sb.append("PREFIX elm: <http://moschetti.org/elm/>");
	sb.append("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>");
	sb.append("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>");
	
	sb.append("SELECT * ");
	sb.append("WHERE {");

	//	sb.append("  x:LMP rdf:type ?type .");

	//sb.append("  ?type ?props ?all .");

	//sb.append("    ?s rdfs:subClassOf elm:Software .");
	//sb.append("    ?s rdfs:subClassOf \"Software\" .");


	sb.append("    elm:someThingElse ?zz ?owners .");
	sb.append("    ?owners elm:age ?age .");

	//sb.append("    ?owners ?props ?x .");
	//sb.append("    FILTER (?age > 20) ");

	sb.append("   }");

        //String queryString = "SELECT * { ?s ?p ?o }" ;
        //String queryString = sb.toString();

        String queryString = "SELECT ?g { GRAPH ?g { }}" ;


        Query query = QueryFactory.create(queryString) ;

        Dataset ds;

	if(true) {

	    // Store store = SDBFactory.connectStore("sdb.ttl") ;
	    //
	    // Must be a DatasetStore to trigger the SDB query engine.
	    // Creating a graph from the Store, and adding it to a general
	    // purpose dataset will not necesarily exploit full SQL generation.
	    // The right answers will be obtained but slowly.
	    //
	    // Dataset ds = DatasetStore.create(store) ;
	    JenaMongoConnection mc = new JenaMongoConnection("mongodb://localhost:27017");
	    JenaMongoStore ms = new JenaMongoStore(mc, "semantic");
	    
	    ds = JenaMongoDataset.create(ms, "uris-full");

	} else {
	    Model mm = ModelFactory.createOntologyModel(); 
	    add(mm, "main", "linksTo", "libA");
	    add(mm, "libA", "linksTo", "libB");
	    ds = DatasetFactory.create(mm);
	}

	System.out.println("ds: " + ds);

        QueryExecution qe = QueryExecutionFactory.create(query, ds) ;

	System.out.println("qe: " + qe);

        try {
            ResultSet rs = qe.execSelect() ;

	    System.out.println("rs: " + rs);

	    int n = 0;
	    while(rs.hasNext()) {
		QuerySolution soln = rs.nextSolution() ;
		System.out.println(soln);
	    }

            //ResultSetFormatter.out(rs) ;

        } finally {
	    qe.close() ;
	}
        
        // Close the SDB conenction which also closes the underlying JDBC connection.
    }

    public static void main(String[] args) {
	(new jena4()).go(args);
    }
}

