/**

The Persistor Experiment

 */

import org.moschetti.jena.mongodb.core.* ;

import org.apache.jena.query.* ;
import org.apache.jena.rdf.model.* ;
import org.apache.jena.rdf.model.impl.PropertyImpl;

public class jena6 {

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

    private void doQuery(Dataset ds, String qs) {
        Query query = QueryFactory.create(qs) ;

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


    private void q1(Dataset ds) {
	StringBuffer sb = new StringBuffer();
	
	//sb.append("PREFIX x: <x:>");
	sb.append("PREFIX buzz: <http://moschetti.org/buzz/>");
	sb.append("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>");
	sb.append("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>");
	
	sb.append("SELECT * ");
	sb.append("WHERE {");

	sb.append("    buzz:Thing buzz:someDouble ?val  . ");

	//	sb.append("    FILTER (?val > 10)  ");
	sb.append("   }");

        String queryString = sb.toString();

	doQuery(ds, queryString);
    }


    private void q2(Dataset ds) {
	StringBuffer sb = new StringBuffer();
	
	//sb.append("PREFIX x: <x:>");
	sb.append("PREFIX buzz: <http://moschetti.org/buzz/>");
	sb.append("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>");
	sb.append("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>");
	
	sb.append("SELECT * ");
	sb.append("WHERE {");

	sb.append("    buzz:Glorp buzz:someObject ?val  . ");

	sb.append("   }");

        String queryString = sb.toString();

	doQuery(ds, queryString);
    }


    public void go(String[] args) {

        Dataset ds;

	Model mm = null;

	JenaMongoConnection mc = new JenaMongoConnection("mongodb://localhost:27017");

	JenaMongoStore ms = new JenaMongoStore(mc, "semantic");

	mm = JenaMongoDataset.createModel(ms, "semtest3");
	ds = DatasetFactory.create(mm);

	//	q1(ds);
	q2(ds);
    }

    public static void main(String[] args) {
	(new jena6()).go(args);
    }
}

