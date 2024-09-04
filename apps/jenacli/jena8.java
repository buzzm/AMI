
import org.moschetti.jena.mongodb.core.* ;

import com.mongodb.client.*;
import com.mongodb.*;
import org.bson.*;

// The Model
import org.apache.jena.rdf.model.* ;

import org.apache.jena.rdf.model.impl.PropertyImpl;

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


public class jena8 {

    public static final String rdf_ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#";
    public static final String rdfs_ns = "http://www.w3.org/2000/01/rdf-schema#";
    public static final String xsd_ns = "http://www.w3.org/2001/XMLSchema#";

    Model mm;
    Dataset ds;

    private void doquery(String qs) {
	try {
	    Query query = QueryFactory.create(qs);

	    try (QueryExecution qexec = QueryExecutionFactory.create(query, ds)) {
		    //try (QueryExecution qexec = QueryExecutionFactory.create(query, mm)) {
		    ResultSet results = qexec.execSelect() ;
		    for ( ; results.hasNext() ; )
			{
			    QuerySolution soln = results.nextSolution() ;
			    System.out.println(soln);
			}
		}

	} catch(Exception e) {
	    System.out.println("epic fail: " + e);
	}
    }

    private void q1() {
	StringBuilder sb = new StringBuilder();
	sb.append("PREFIX a: <http://moschetti.org/elm/> \n");
	sb.append("PREFIX buzz: <http://moschetti.org/buzz/> \n");
	sb.append("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> \n");
	sb.append("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> \n");
	sb.append("PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> \n");
	
	sb.append("SELECT * \n");
	sb.append("WHERE { \n");
	sb.append(" ?s rdfs:subClassOf a:Software . \n");
	sb.append("}");
	
	String qs = sb.toString();
	
	doquery(qs);
    }


    private void q2() {
	StringBuilder sb = new StringBuilder();
	sb.append("PREFIX a: <http://moschetti.org/elm/> \n");
	sb.append("PREFIX buzz: <http://moschetti.org/buzz/> \n");
	sb.append("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> \n");
	sb.append("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> \n");
	sb.append("PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> \n");
	
	sb.append("SELECT * \n");
	sb.append("WHERE { \n");
	sb.append(" ?s buzz:isGrimble ?o . \n");
	sb.append("}");
	
	String qs = sb.toString();
	
	doquery(qs);
    }

    private void add(String s, String p, String o) {
	mm.add(ResourceFactory.createStatement(
			  new PropertyImpl(s),
			  new PropertyImpl(p),
			  new PropertyImpl(o))
		  );
    }

    public void go(String[] args) {
	JenaMongoConnection mc = new JenaMongoConnection("mongodb://localhost:27017");
	JenaMongoStore ms = new JenaMongoStore(mc, "semantic");

	mm = JenaMongoDataset.createModel(ms, "test4");
	ds = DatasetFactory.create(mm);

	q1();
	q2();

	String elm_ns = "http://moschetti.org/elm/";
	String data_ns = "http://moschetti.org/buzz/";

	//db[targetCollname].insert({"S":C, "P":"rdf:type", "O":"rdfs:Class"});
	//db[targetCollname].insert({"S":C, "P":"rdfs:subClassOf", "O":P});

	/*
	add(elm_ns + "Neo4J", rdf_ns + "type", rdfs_ns + "Class");

	//  THIS is what will trigger the reasoner to re-read ALL the
	//  rdfs:subClassOf props from the DB....
	*/

	add(elm_ns + "Neo4J", rdfs_ns + "subClassOf", elm_ns + "DB");



	// TOSCA
	// apache tinkerpup

	/*
	Scanner console = new Scanner(System.in);
	System.out.print("ENTER to continue> ");
	String cmd = console.nextLine();
	*/


	//add(data_ns + "Corndog", data_ns + "validates", data_ns + "zoop");

	System.out.println("2nd round");
	q1();
	q2();

    }

    public static void main(String[] args) {
	(new jena8()).go(args);
    }


}
