
/**

http://tutorial-academy.com/ontology-traversal-jena-sparql/
verum.com

/Users/buzz/java/lib/mongo-java-driver-3.4.2.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/jena-core-3.4.0.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/jena-base-3.4.0.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/jena-iri-3.4.0.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/jena-arq-3.4.0.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/jena-shaded-guava-3.4.0.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/slf4j-api-1.7.25.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/slf4j-log4j12-1.7.25.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/log4j-1.2.17.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/xercesImpl-2.11.0.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/xml-apis-1.4.01.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/libthrift-0.9.3.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/httpclient-4.5.3.jar
/Users/buzz/Downloads/apache-jena-3.4.0/lib/commons-lang3-3.4.jar


java -classpath .:/Users/buzz/java/lib/mongo-java-driver-3.4.2.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/jena-core-3.4.0.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/jena-base-3.4.0.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/jena-iri-3.4.0.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/jena-arq-3.4.0.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/jena-shaded-guava-3.4.0.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/slf4j-api-1.7.25.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/slf4j-log4j12-1.7.25.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/log4j-1.2.17.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/xercesImpl-2.11.0.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/xml-apis-1.4.01.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/libthrift-0.9.3.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/httpclient-4.5.3.jar:/Users/buzz/Downloads/apache-jena-3.4.0/lib/commons-lang3-3.4.jar jena1 mongodb://localhost:27017 sparql1.spq


 */

import com.mongodb.client.result.UpdateResult;
import com.mongodb.client.*;
import com.mongodb.*;
import org.bson.*;

// The Model
import org.apache.jena.ontology.OntModel;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdf.model.ResourceFactory;
import org.apache.jena.rdf.model.Statement;
import org.apache.jena.rdf.model.Resource;
import org.apache.jena.rdf.model.Property;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.rdf.model.impl.PropertyImpl;

// For date->XSDDateTime conversion:
import org.apache.jena.datatypes.xsd.XSDDateTime;
import java.util.Calendar;

    
// The SPARQ engine that consumes the model
import org.apache.jena.query.* ;


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


public class jena1 {

    static OntModel model = null;

    public static MongoDatabase db;

    //public static final String pfx = "a://x/";
    public static final String pfx = "a:";


    public static final String rdf_uri = "http://www.w3.org/1999/02/22-rdf-syntax-ns#";
    public static final String rdfs_uri="http://www.w3.org/2000/01/rdf-schema#";


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

    private static void rebuild() {
	// Clobber old model:
	model = ModelFactory.createOntologyModel(); 

	MongoCollection<BsonDocument> coll;

	System.out.println("slurp model");
	coll = db.getCollection("elm_model", BsonDocument.class);
	slurpColl(coll);

	System.out.println("slurp data");
	coll = db.getCollection("elm", BsonDocument.class);
	slurpColl(coll);
    }


    private static void slurpColl(MongoCollection<BsonDocument> coll) {
	BsonDocument doc = null;

	try {
	    java.util.Date start = new java.util.Date();

	    int num = 0;
	    MongoCursor cc = coll.find().iterator();  // slurp!

	    while(cc.hasNext()) {
		doc = (BsonDocument) cc.next();
		
		//Resource subject = new PropertyImpl(doc.getString("S").getValue());
		String ss = makeResource(doc.getString("S").getValue());
		Resource subject = new PropertyImpl(ss);

		String pp = makeResource(doc.getString("P").getValue());
		Property predicate = new PropertyImpl(pp);

		
		//Resource object = new PropertyImpl();
	    
		//System.out.println("HERE1");
		//Statement s = ResourceFactory.createStatement(subject, predicate, object);
		//System.out.println("HERE2");
		//model.add(s); // add the statement (triple) to the model

		// The BsonDocument getValue() return a type-correct java native
		// value for which most things work...

		//System.out.println(doc);

		Object bo = null;
		Object o = null;
		BsonValue vv = doc.get("O");

		BsonType bt = vv.getBsonType();

		if(bt == BsonType.STRING) {
		    String sobj = ((BsonString)vv).getValue();

		    if('!' == sobj.charAt(0)) {
			String xs = sobj.substring(1,sobj.length());
			model.addLiteral(subject, predicate, xs);
		    } else {
			Resource object = new PropertyImpl(makeResource(sobj));
			model.add(ResourceFactory.createStatement(subject, predicate, object));
		    }
		} else {
		    switch(bt) {
		    case INT32:
			bo = vv.asInt32();
			o = ((BsonInt32)bo).getValue();
			break;
		    case INT64:
			bo = vv.asInt64();
			o = ((BsonInt64)bo).getValue();
			break;
		    case DOUBLE:
			bo = vv.asDouble();
			o = ((BsonDouble)bo).getValue();
			break;

		    case BOOLEAN:
			bo = vv.asBoolean();
			o = (boolean) ((BsonBoolean)bo).getValue();
			break;

		    case DATE_TIME:
			bo = vv.asDateTime();
			long tv = ((BsonDateTime)bo).getValue(); // ms since epoch
			/*
			We want our literals to be as standard as possible;
			remember our lesson from cheating with rdf:type
			and rdfs:subClassOf.  This will make datetimes 
			look like 
			   "2016-07-06T00:00:00Z"^^xsd:dateTime
			instead of 
			   "Thu Dec 31 19:00:00 EST 2015"^^<java:java.util.Date>
			or
			   "BsonDateTime{value=1577836800000}"^^<java:org.bson.BsonDateTime>
			It is cool how class runtime props are picked up but
			clearly various built-in comparators and tools are 
			going to be looking for xsd:dateTime
			*/
			Calendar cal = Calendar.getInstance();
			cal.setTimeInMillis(tv);
			o = new XSDDateTime(cal); // from the Jena lib itself

			break;

		    case DOCUMENT:
			System.out.println("yo: " + vv);
			o = vv;
			break;

		    default:
			o = vv.toString();
			break;
		    }
		    model.addLiteral(subject, predicate, o);
		}

		num++;
		if(0 == num % 50000) {
		    System.out.println(num);
		}
	    }
	
	    cc.close();

	    java.util.Date end = new java.util.Date();
	    long diff = end.getTime() - start.getTime();
	    System.out.println(num + " slurped in " + diff + " ms");

	} catch(Exception e) {
	    System.out.println("loadDB fail: " + e);
	    System.out.println("doc: " + doc);
	    e.printStackTrace();
	}
    }

    private static void add(OntModel m, String s, String p, String o) {
	m.add(ResourceFactory.createStatement(
			  new PropertyImpl(makeResource(s)),
			  new PropertyImpl(makeResource(p)),
			  new PropertyImpl(makeResource(o)))
		  );
    }

    public static void main(String[] args) {

	try {
	    // This seems to generate a warning...?
	    model = ModelFactory.createOntologyModel(); 

	    String filename = null;

	    if(args.length == 2) { // connstring, file
		String conns = args[0];

		System.out.println("open conn " + conns);
		MongoClient mongoClient = new MongoClient(new MongoClientURI(conns));
		System.out.println("opened");

		//DB db = mongoClient.getDB( "mydb" );
		db = mongoClient.getDatabase( "semantic" );

		rebuild();

		filename = args[1];

	    } else {
		filename = args[0];

		Resource subject;
		Property predicate;
		Resource object;

		/*
		java.util.Date start = new java.util.Date();
		int max = 1000000;   // about 3.2 seconds for 1,000,000 triples
		for(int i = 0; i < max; i++) {
		    subject = new PropertyImpl("buzz" + i);
		    predicate = new PropertyImpl(makeResource("isA"));
		    model.addLiteral(subject, predicate, "person");
		}
		java.util.Date end = new java.util.Date();
		long diff = end.getTime() - start.getTime();
		System.out.println(max + " model adds in " + diff + " ms");
		*/

		add(model, "main", "linksTo", "libA");
		add(model, "libA", "linksTo", "libB");
		add(model, "libB", "linksTo", "libC");
		add(model, "libB", "linksTo", "libD");
		add(model, "libB", "linksTo", "libE");

		add(model, "libA", "linksTo", "libE");

		add(model, "libC", "linksTo", "libF");
		add(model, "libF", "linksTo", "libG");
		add(model, "libG", "linksTo", "libH");

		subject = new PropertyImpl("ace5:r:foo");
		predicate = new PropertyImpl("ace5:p:foo");
		object = new PropertyImpl("ace5:r:bar");
		model.add(ResourceFactory.createStatement(subject, predicate, object));
	    }

	    Scanner console = new Scanner(System.in);

	    while(true) {
		System.out.print("X to reslurp; ENTER to read " + filename + "> ");
		String cmd = console.nextLine();
		if("X".equals(cmd)) {
		    rebuild();
		    continue;
		}


		String queryString = new Scanner(new File(filename)).useDelimiter("\\Z").next();
		
		//System.out.println("exec:" + queryString);
		
		Query query = QueryFactory.create(queryString);
		try (QueryExecution qexec = QueryExecutionFactory.create(query, model)) {
			ResultSet results = qexec.execSelect() ;
			for ( ; results.hasNext() ; )
			    {
				QuerySolution soln = results.nextSolution() ;
				System.out.println(soln);
				
				/*
				java.util.Iterator<String> vn = soln.varNames();
				while(vn.hasNext()) {
				    String n = vn.next();
				    RDFNode x = soln.get(n);
				    System.out.println(n + ": " + x);
				}
				*/
				//RDFNode x = soln.get("a") ;       // Get a result variable by name.
				//Resource r = soln.getResource("things") ; // Get a result variable - must be a resource
				//System.out.println("things: " + r);
				
				//Literal l = soln.getLiteral("VarL") ;   // Get a result variable - must be a literal
			    }
		    }
	    }
		

	} catch(Exception e) {
	    System.out.println("epic fail: " + e);
	}
    }


}
