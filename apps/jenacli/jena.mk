JAVAC		= javac

JL		= $(HOME)/java/lib

#MONGO_DRIVER	= $(JL)/mongo-java-driver-3.4.2.jar
MDRV_VERS	= 4.9.0
MONGO_DRIVER	= $(JL)/mongodb-driver-sync-$(MDRV_VERS).jar:$(JL)/mongodb-driver-core-$(MDRV_VERS).jar:$(JL)/bson-$(MDRV_VERS).jar

#  Jena 3.4
JMDB		= $(JL)/jena-mongodb-3.4.jar
JENAL		= $(HOME)/codes/apache-jena-3.4.0/lib
JENAJ		= $(JENAL)/jena-core-3.4.0.jar:$(JENAL)/jena-base-3.4.0.jar:$(JENAL)/jena-iri-3.4.0.jar:$(JENAL)/jena-arq-3.4.0.jar:$(JENAL)/jena-shaded-guava-3.4.0.jar:$(JENAL)/slf4j-api-1.7.25.jar:$(JENAL)/slf4j-log4j12-1.7.25.jar:$(JENAL)/log4j-1.2.17.jar:$(JENAL)/xercesImpl-2.11.0.jar:$(JENAL)/xml-apis-1.4.01.jar:$(JENAL)/libthrift-0.9.3.jar:$(JENAL)/httpclient-4.5.3.jar:$(JENAL)/commons-lang3-3.4.jar


#  Jena 5.1
JMDB		= $(JL)/jena-mongodb-5.1.jar
JENAL		= $(HOME)/codes/apache-jena-5.1.0/lib
JENAJ		= $(JENAL)/RoaringBitmap-1.2.0.jar:$(JENAL)/apiguardian-api-1.1.2.jar:$(JENAL)/caffeine-3.1.8.jar:$(JENAL)/collection-0.7.jar:$(JENAL)/commons-cli-1.8.0.jar:$(JENAL)/commons-codec-1.17.0.jar:$(JENAL)/commons-collections4-4.4.jar:$(JENAL)/commons-compress-1.26.2.jar:$(JENAL)/commons-csv-1.11.0.jar:$(JENAL)/commons-io-2.16.1.jar:$(JENAL)/commons-lang3-3.14.0.jar:$(JENAL)/error_prone_annotations-2.27.0.jar:$(JENAL)/gson-2.11.0.jar:$(JENAL)/jakarta.json-2.0.1.jar:$(JENAL)/jcl-over-slf4j-2.0.13.jar:$(JENAL)/jena-arq-5.1.0.jar:$(JENAL)/jena-base-5.1.0.jar:$(JENAL)/jena-cmds-5.1.0.jar:$(JENAL)/jena-core-5.1.0.jar:$(JENAL)/jena-dboe-base-5.1.0.jar:$(JENAL)/jena-dboe-index-5.1.0.jar:$(JENAL)/jena-dboe-storage-5.1.0.jar:$(JENAL)/jena-dboe-trans-data-5.1.0.jar:$(JENAL)/jena-dboe-transaction-5.1.0.jar:$(JENAL)/jena-iri-5.1.0.jar:$(JENAL)/jena-ontapi-5.1.0.jar:$(JENAL)/jena-rdfconnection-5.1.0.jar:$(JENAL)/jena-rdfpatch-5.1.0.jar:$(JENAL)/jena-shacl-5.1.0.jar:$(JENAL)/jena-shex-5.1.0.jar:$(JENAL)/jena-tdb1-5.1.0.jar:$(JENAL)/jena-tdb2-5.1.0.jar:$(JENAL)/junit-platform-commons-1.10.3.jar:$(JENAL)/junit-platform-engine-1.10.3.jar:$(JENAL)/junit-platform-launcher-1.10.3.jar:$(JENAL)/junit-platform-suite-api-1.10.3.jar:$(JENAL)/junit-platform-suite-commons-1.10.3.jar:$(JENAL)/junit-platform-suite-engine-1.10.3.jar:$(JENAL)/libthrift-0.20.0.jar:$(JENAL)/log4j-api-2.23.1.jar:$(JENAL)/log4j-core-2.23.1.jar:$(JENAL)/log4j-slf4j2-impl-2.23.1.jar:$(JENAL)/opentest4j-1.3.0.jar:$(JENAL)/protobuf-java-4.27.2.jar:$(JENAL)/slf4j-api-2.0.13.jar:$(JENAL)/titanium-json-ld-1.4.0.jar

OTHER		= $(JL)/json-20240303.jar

CLASSPATH	= .:$(MONGO_DRIVER):$(JMDB):$(JENAJ):$(OTHER)

CLASSES		= \
	jena1.class \
	jena2.class \
	jena3.class \
	jena4.class \
	jena5.class \
	jena6.class \
	jena7.class \
	jena8.class


.SUFFIXES:	.java .class

.java.class:
	$(JAVAC) -classpath $(CLASSPATH) $<


all:	$(CLASSES)


clean:
	/bin/rm -f *.class *~


