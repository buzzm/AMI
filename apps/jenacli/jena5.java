/**

The Persistor Experiment

 */

// The SPARQ engine that consumes the model
import org.moschetti.jena.mongodb.core.* ;

import org.apache.jena.query.* ;
import org.apache.jena.rdf.model.* ;
import org.apache.jena.rdf.model.impl.PropertyImpl;

public class jena5 {

    public static final String rdf_pfx = "http://www.w3.org/1999/02/22-rdf-syntax-ns#";
    public static final String rdfs_pfx="http://www.w3.org/2000/01/rdf-schema#";

    public static final String elm_pfx = "http://moschetti.org/buzz/";


    public static String makeResource(String val) {
	return val;
    }

    private static void add(Model m, String s, String p, String o) {
	Statement sss = ResourceFactory.createStatement(
			  new PropertyImpl(makeResource(s)),
			  new PropertyImpl(makeResource(p)),
			  new PropertyImpl(makeResource(o)));
	m.add(sss);
    }

    private static void qqc(Model mm, String C, String P) {
	add(mm, elm_pfx + C, rdf_pfx + "type", rdfs_pfx + "Class");
	add(mm, elm_pfx + C, rdfs_pfx + "subClassOf", elm_pfx + P);
    }



    public void go(String[] args) {

	StringBuffer sb = new StringBuffer();
	
	//sb.append("PREFIX x: <x:>");
	sb.append("PREFIX buzz: <http://moschetti.org/buzz/>");
	sb.append("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>");
	sb.append("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>");
	
	sb.append("SELECT * ");
	sb.append("WHERE {");

	sb.append("    ?s rdfs:subClassOf buzz:A . ");

	sb.append("   }");

        String queryString = sb.toString();

        Query query = QueryFactory.create(queryString) ;

        Dataset ds;

	Model mm = null;
	
	if(true) {
	    JenaMongoConnection mc = new JenaMongoConnection("mongodb://localhost:27017");
	    JenaMongoStore ms = new JenaMongoStore(mc, "semantic");
	    
	    //ds = JenaMongoDataset.create(ms, "semtest1");

	    mm = JenaMongoDataset.createModel(ms, "semtest2");

	    qqc(mm, "E", "D");

	    ds = DatasetFactory.create(mm);

	} else {
	    mm = ModelFactory.createOntologyModel(); 

	    qqc(mm, "A", "Item");
	    qqc(mm, "B", "A");
	    qqc(mm, "B2", "A");
	    qqc(mm, "C", "B");
	    qqc(mm, "D", "C");

	    qqc(mm, "X", "Item");
	    qqc(mm, "Y", "X");
	    qqc(mm, "Z", "Y");

	    ds = DatasetFactory.create(mm);
	}

	doQuery(ds, query);

	doQuery(ds, query);
    }

    private void doQuery(Dataset ds, Query query) {
	java.util.Date start = new java.util.Date();

        QueryExecution qe = QueryExecutionFactory.create(query, ds) ;

        try {
            ResultSet rs = qe.execSelect() ;

	    int n = 0;
	    while(rs.hasNext()) {
		QuerySolution soln = rs.nextSolution() ;
		System.out.println(soln);
	    }

            //ResultSetFormatter.out(rs) ;

        } finally {
	    qe.close() ;
	}

	java.util.Date end = new java.util.Date();

	long diff = end.getTime() - start.getTime();

	System.out.println(diff + " ms");
    }

    public static void main(String[] args) {
	(new jena5()).go(args);
    }
}

