
/**

 */

import com.mongodb.client.result.UpdateResult;
import com.mongodb.client.*;
import com.mongodb.*;
import org.bson.*;

// The Model
import org.apache.jena.ontology.OntModel;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.InfModel;
import org.apache.jena.rdf.model.ModelFactory;

import org.apache.jena.rdf.model.ResourceFactory;

import org.apache.jena.rdf.model.Statement;
import org.apache.jena.rdf.model.StmtIterator;

import org.apache.jena.rdf.model.Resource;
import org.apache.jena.rdf.model.Property;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.rdf.model.impl.PropertyImpl;
import org.apache.jena.rdf.model.impl.ResourceImpl;

import org.apache.jena.vocabulary.RDF;
import org.apache.jena.vocabulary.RDFS;

import org.apache.jena.util.PrintUtil;

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


public class jena2 {

    public static void printStatements(String tag, Model m, Resource s, Property p, Resource o) {
	System.out.println(tag);
	for (StmtIterator i = m.listStatements(s,p,o); i.hasNext(); ) {
	    Statement stmt = i.nextStatement();
	    //System.out.println(stmt);
	    System.out.println(" - " + PrintUtil.print(stmt));
	}
    }

    private static void addRaw(OntModel m, Resource s, Property p, Resource o) {
	m.add(ResourceFactory.createStatement(s, p, o));
    }

    public static void main(String[] args) {
	OntModel model = ModelFactory.createOntologyModel(); 

	// Basic items:
	addRaw(model, new ResourceImpl("x:Item"), RDF.type, RDFS.Class);
	addRaw(model, new ResourceImpl("x:Item"), new PropertyImpl("x:owner"), new ResourceImpl("x:someone"));
	
	addRaw(model, new ResourceImpl("x:SW"), RDF.type, RDFS.Class);
	addRaw(model, new ResourceImpl("x:SW"), RDFS.subClassOf, new ResourceImpl("x:Item"));
	addRaw(model, new ResourceImpl("x:SW"), new PropertyImpl("x:eol"), new ResourceImpl("x:somedate"));
	addRaw(model, new ResourceImpl("x:SW"), new PropertyImpl("x:foundry"), new ResourceImpl("x:brpbrp"));
	
	addRaw(model, new ResourceImpl("x:Exec"), RDF.type, RDFS.Class);
	addRaw(model, new ResourceImpl("x:Exec"), RDFS.subClassOf, new ResourceImpl("x:SW"));
	addRaw(model, new ResourceImpl("x:Exec"), new PropertyImpl("x:connectsOn"), new ResourceImpl("x:somewhere"));
	addRaw(model, new ResourceImpl("x:Exec"), new PropertyImpl("x:connectsTo"), new ResourceImpl("x:something"));
	addRaw(model, new ResourceImpl("x:Exec"), new PropertyImpl("x:deployedOn"), new ResourceImpl("x:somehost"));


	addRaw(model, new ResourceImpl("x:LMP"), RDF.type, new ResourceImpl("x:Exec"));
	addRaw(model, new ResourceImpl("x:LMP"), new PropertyImpl("x:userThreshold"), new ResourceImpl("x:zippy"));


	/*
	addRaw(model, new ResourceImpl("x:Lib"), RDF.type, RDFS.Class);
	addRaw(model, new ResourceImpl("x:Lib"), RDFS.subClassOf, new ResourceImpl("x:SW"));
	
	addRaw(model, new ResourceImpl("x:Device"), RDF.type, RDFS.Class);
	addRaw(model, new ResourceImpl("x:Device"), RDFS.subClassOf, new ResourceImpl("x:Item"));
	
	addRaw(model, new ResourceImpl("x:Host"), RDF.type, RDFS.Class);
	addRaw(model, new ResourceImpl("x:Host"), RDFS.subClassOf, new ResourceImpl("x:Device"));
	
	addRaw(model, new ResourceImpl("x:VM"), RDF.type, RDFS.Class);
	addRaw(model, new ResourceImpl("x:VM"), RDFS.subClassOf, new ResourceImpl("x:Host"));
	addRaw(model, new ResourceImpl("x:VM"), new PropertyImpl("x:procs"), new ResourceImpl("x:FOUR"));
	

	addRaw(model, new ResourceImpl("x:App1"), RDF.type, RDFS.Class);
	addRaw(model, new ResourceImpl("x:App1"), RDFS.subClassOf, new ResourceImpl("x:Exec"));
	addRaw(model, new ResourceImpl("x:App1"), new PropertyImpl("x:grimble"), new ResourceImpl("x:brp"));

	addRaw(model, new ResourceImpl("x:guava"), RDF.type, RDFS.Class);
	addRaw(model, new ResourceImpl("x:guava"), RDFS.subClassOf, new ResourceImpl("x:Lib"));
	addRaw(model, new ResourceImpl("x:guava"), new PropertyImpl("x:type"), new ResourceImpl("x:Java"));

	
	addRaw(model, new ResourceImpl("x:MBus"), RDF.type, RDFS.Class);
	addRaw(model, new ResourceImpl("x:MBus"), RDFS.subClassOf, new ResourceImpl("x:Exec"));

	addRaw(model, new ResourceImpl("x:Instance"), RDF.type, RDFS.Class);
	// no subClass
	*/


	{  // as type only
	    System.out.println("type of atom, not rdf:Class");
	    addRaw(model, new ResourceImpl("x:VM_123"), RDF.type, new ResourceImpl("x:VM"));
	    //addRaw(model, new ResourceImpl("x:VM_123"), RDF.type, new ResourceImpl("x:Instance"));


	    addRaw(model, new ResourceImpl("x:VM_124"), RDF.type, new ResourceImpl("x:VM"));
	    //addRaw(model, new ResourceImpl("x:VM_124"), RDF.type, new ResourceImpl("x:Instance"));


	    addRaw(model, new ResourceImpl("x:LMP_887"), RDF.type, new ResourceImpl("x:LMP"));
	    //addRaw(model, new ResourceImpl("x:LMP_887"), RDF.type, new ResourceImpl("x:Instance"));
	    addRaw(model, new ResourceImpl("x:LMP_887"), new PropertyImpl("x:deployedTo"), new ResourceImpl("x:VM_123"));
	}


	{
	    String rname = "x:LMP_887";
	    Resource ww1 = model.getResource(rname);

	    //a:LMP_887 ?p  ?o

	    //printStatements("X1", model, ww1, null, null);
	}

	/*
	{
	    String rname = "x:widget";

	    Resource ww1 = model.getResource(rname);
	    printStatements("A", model, ww1, RDF.type, null);

	    printStatements("A", model, ww1, RDF.type, null);
	    printStatements("B", model, ww1, null, null);

	    Resource ww2 = infmodel.getResource(rname);
	    printStatements("C", infmodel, ww2, RDF.type, null);
	    printStatements("D", model, ww2, null, null);
	}
	*/

	if(true) {

	    StringBuffer sb = new StringBuffer();
	    
	    sb.append("PREFIX x: <x:>");
	    sb.append("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>");
	    sb.append("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>");
	    
	    sb.append("SELECT *");
	    sb.append("WHERE {");


	    sb.append("  x:LMP rdf:type ?type .");
	    sb.append("  ?type ?props ?all .");
	    sb.append("   MINUS {");
	    sb.append("     rdfs:Resource ?props ?all .");
	    sb.append("   }");


	    /*
	    sb.append("  ?s rdfs:subClassOf x:Instance ;");
	    sb.append("     rdfs:subClassOf x:SW .");
	    sb.append("  ?s ?props ?all .");
	    */

	    //sb.append("  ?s rdfs:subClassOf x:Instance .");
	    //sb.append("     rdf:type        x:Device .");
	    //	    sb.append("        x:exec       x:LMP .");
	    //sb.append("  ?s x:exec* x:SW .");

	    //sb.append("  ?s rdf:type x:Exec .");

	    // Show all SW:
	    //sb.append("  ?s rdfs:subClassOf x:SW .");

	    // Show all Device:
	    //sb.append("  ?s rdfs:subClassOf x:Device .");


	    //sb.append("  ?s ?props ?all .");

	    /*
	    sb.append("  x:LMP rdf:type ?type .");
	    sb.append("  ?type ?props ?all .");
	    */

	    //sb.append("  x:B ?props ?all .");
	    //sb.append("  ?s ?p ?o .");

	    sb.append("}");
	    
	    Query query = QueryFactory.create(sb.toString());
	    try (QueryExecution qexec = QueryExecutionFactory.create(query, model)) {
		    ResultSet results = qexec.execSelect() ;
		    for ( ; results.hasNext() ; ) {
			QuerySolution soln = results.nextSolution() ;
			System.out.println(soln);
		    }
		} catch(Exception e) {
		System.out.println("epic fail: " + e);
	    }
	}
    }
}
