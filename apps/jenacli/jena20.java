
import org.apache.jena.query.*;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.sdb.SDBFactory;
import org.apache.jena.sdb.Store;
import org.apache.jena.sdb.StoreDesc;
import org.apache.jena.sdb.sql.SDBConnection;
import org.apache.jena.sdb.store.DatabaseType;
import org.apache.jena.sdb.layout2.LayoutType;

public class JenaMixedPrefixesExample {

    public static void main(String[] args) {
        // Configure and connect to the first PostgreSQL database
        StoreDesc storeDescAmiAmix =3D new StoreDesc(LayoutType.LayoutTriple=
NodesHash, DatabaseType.PostgreSQL);
        SDBConnection connAmiAmix =3D new SDBConnection("jdbc:postgresql://l=
ocalhost/rdfdb_ami_amix", "username", "password");
        Store storeAmiAmix =3D SDBFactory.connectStore(connAmiAmix, storeDes=
cAmiAmix);
        Dataset datasetAmiAmix =3D SDBFactory.connectDataset(storeAmiAmix);

        // Configure and connect to the second PostgreSQL database
        StoreDesc storeDescEx =3D new StoreDesc(LayoutType.LayoutTripleNodes=
Hash, DatabaseType.PostgreSQL);
        SDBConnection connEx =3D new SDBConnection("jdbc:postgresql://localh=
ost/rdfdb_ex", "username", "password");
        Store storeEx =3D SDBFactory.connectStore(connEx, storeDescEx);
        Dataset datasetEx =3D SDBFactory.connectDataset(storeEx);

        // Combine the models from both datasets
        Model modelAmiAmix =3D datasetAmiAmix.getDefaultModel();
        Model modelEx =3D datasetEx.getDefaultModel();

        // Create a new dataset to hold the combined data
        Dataset combinedDataset =3D DatasetFactory.create();
        combinedDataset.setDefaultModel(modelAmiAmix.union(modelEx));

        // SPARQL query that mixes both prefixes
        String sparqlQuery =3D """
            PREFIX ami: <http://example.org/ami#>
            PREFIX ex: <http://example.org/ex#>
           =20
            SELECT ?app ?creator
            WHERE {
              ex:myApp ami:createdBy ?creator .
            }
            """;

        // Execute the query on the combined dataset
        Query query =3D QueryFactory.create(sparqlQuery);
        try (QueryExecution qexec =3D QueryExecutionFactory.create(query, co=
mbinedDataset)) {
            ResultSet results =3D qexec.execSelect();
            ResultSetFormatter.out(System.out, results, query);
        }

        // Close the stores and connections
        storeAmiAmix.close();
        storeEx.close();
    }
}

