
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


public class jena3 {

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

	Resource A = ResourceFactory.createResource("x:A");
	Resource B = ResourceFactory.createResource("x:B");
	Property prop1 = ResourceFactory.createProperty("x:prop1");
	Property prop2 = ResourceFactory.createProperty("x:prop2");
	Resource whatever = ResourceFactory.createResource("x:whatever");
	Resource other = ResourceFactory.createResource("x:other");
	Resource widget = ResourceFactory.createResource("x:widget");

	addRaw(model, A, RDF.type, RDFS.Class);
	addRaw(model, A, prop1, whatever);
	addRaw(model, B, RDF.type, RDFS.Class);
	addRaw(model, B, prop2, other);
	addRaw(model, B, RDFS.subClassOf, A);
	addRaw(model, widget, RDF.type, B);

	StringBuffer sb = new StringBuffer();

	sb.append("PREFIX x: <x:>");
	sb.append("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>");
	sb.append("SELECT * {");
	sb.append("  x:widget rdf:type ?type .");
	sb.append("  ?type ?props ?all .");
	sb.append("}");

	Query query = QueryFactory.create(sb.toString());
	try (QueryExecution qexec = QueryExecutionFactory.create(query, model)) {
		ResultSet results = qexec.execSelect();
		for (; results.hasNext(); ) {
		    QuerySolution soln = results.nextSolution();
		    System.out.println(soln);
		}
	    } catch (Exception e) {
	    System.out.println("epic fail: " + e);
	}
    }
}

