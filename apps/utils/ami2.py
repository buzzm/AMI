
#from langchain.chat_models import ChatOpenAI  # deprecated 
#from langchain_community.chat_models import ChatOpenAI

from langchain_openai import ChatOpenAI

#from langchain.llms import OpenAI # import OpenAI model

from langchain.chains import LLMChain, ConversationChain
from langchain.memory import ConversationBufferMemory

#from langchain.prompts import ChatPromptTemplate, PromptTemplate # import PromptTemplate
import openai

import datetime
import time
import json
import os
import re
import sys
import argparse

#  https://github.com/microsoft/azurechatgpt
#  https://news.ycombinator.com/item?id=37112741

class Program():
    def __init__(self, conversation, fd, rargs):
        self.conversation = conversation
        self.fd = fd
        self.rargs = rargs


    def ask(self, blurb,echo=True):
        if echo is True:
            print("ME:", blurb)
        xx = self.conversation.predict(input=blurb)
        #print("ChatGPT:", xx)
        print(xx)
        print()

    def init_system(self):
        ami_meta_f = "/Users/buzz/git/AMI/ami.ttl"
        with open(ami_meta_f) as fd:
            ami_meta = fd.read()

        print("Initializing system with model %s ..." % self.rargs.model)

        blocks = [
    {"lbl":"Overall Design", "txt":"""
This an overall design summary of the AMI System:
 *  AMI is based on RDF triples

 *  The main classes are Software, Hardware, Shape, Component, and System.

 *  Software has a property "linksWith" whose value is another Software instance.
    This is how recursive dependencies can be constructed.  Multiple "linksWith"
    properties are of course supported.

 *  Components define interfaces and declare their dependencies with the
    "connectsTo" property whose value is another Component.  This is how a multi
    component system can be built.  Components are an "abstract" representation
    of functionality and data Shape flow but they do not define specific Software or
    Hardware.

 *  A critical feature is that Software and Hardware may have a property "implements"
    whose value is a Component.  This is what binds an abstract definition of a system
    to the actual code and hardware that runs it.  Again, components do *NOT* define
    their Software; instead, Software *implements* a Component.

 *  A System is an administrative "starting point" for a cooperating collection of
    Components.  A System does not have to name all the components.  Typically, the
    "top-most" application component is named and dependent components can be derived
    from the "connectsTo" property.  Systems are typically how the business and a
    technical manager organize the technology footprint.
    """}

    ,{"lbl":"AMI Metadata", "txt":"""
Below is a set of RDF triples in turtle format that define a set of
classes and properties that show relationships between software, hardware, and data.
It is the
metadata for the AMI system.  AMI specific classes and properties are placed in
the `ami:` and `sh:` prefix namespaces.
The metadata ends when you see the line `# END METADATA`.

%s

# END METADATA
"""  % ami_meta}


    ,{"lbl":"Assumptions and Instructions", "txt":"""
Here are important assumptions and instructions:
 *  You will use your knowledge of SPARQL and the AMI metadata to be able to
    produce SPARQL queries.

 *  ALWAYS create a response that has 2 parts:
    1.  The SPARQL statement
    2.  Textual insightful narrative about how you created the SPARQL statement
        including notes on how you interpreted the question.
    The narrative will be lines of text no longer than 60 characters.
    EVERY narrative line is preceded with the hash (#) character.
    For example, when asked:
        "Please group the assets by manager and print a list of manager and
        total number of assets for that manager only if the total is greater
        than 2, and sort by total"
    your response should be similar to this:
        # AMI assumes that to "manage" an item means to the be the owner of it.
        # This is different from the steward who has operational responsibility,
        # not overall responsibility.
        SELECT ?owner (COUNT(?item) AS ?totalAssets)
        WHERE {
          ?item ami:owner ?owner .
        }
        GROUP BY ?owner
        HAVING (COUNT(?item) > 2)
        ORDER BY DESC(?totalAssets)

    
 *  DO NOT use the clause `?item a ami:Item` in the construction of any query.
    We do not use RDFS reasoning in AMI to avoid potentially imprecise inference.

 *  ABSOLUTELY DO NOT invent RDF predicates in your SPARQL responses.  All predicates MUST come from
    the supplied 'ami:' or 'sh:' prefixes.  If you cannot do so, you must ask for
    more information.

 *  ASSUME that specific instance subjects and objects are in the 'ex:' namespace.
    For example to find properties of system "system_001":
        SELECT *
        WHERE {
            ex:system_001 a ami:System .
        }
    
 *  ASSUME that unquoted identifiers entities imply URIs, not literal strings or
    unbound variables.  For example, given the following question:
        Show everything that depends on software lib77
    it should be interpreted as 
        Show everything that depends on software instance ex:lib77
    
    
 *  DO rely on the "rdfs:label" property, if it exists, to provide a general identifier
    of a thing (software, hardware, component, etc.) without getting into details of
    version.  For example, you will get questions like "Where do we use log4j?"; you
    can use the "rdfs:label" property as a "tag" to help you identify the correct
    properties and classes to use in the SPARQL statement.

 *  DO rely on the "rdfs:comment" property, if it exists, to provide very accurate
    textual detail of a entity, which will help you associate the natural language
    question with the correct properties and classes to use in the SPARQL statement.

 *  When presented with very broad questions like:
        "What software is used for risk?"
        "Show me everything that makes graphics"
    then DO identify keywords and filter against `rdfs:comment` as follows:
        ?subject rdfs:comment ?comments ;
        FILTER(REGEX(?comment, "keyword", "i"))

    
 *  DO associate the noun "asset" with any of type "ami:Software", "ami:Hardware",
    or "ami:Shape".
    
 *  DO associate the noun "software" with type "ami:Software"
 *  DO associate the noun "hardware" with type "ami:Hardware"    
 *  DO associate the phrase "depends on" in the context of software with the predicate "ami:linksWith"
 *  DO associate the phrase "depends on" in the context of components with the predicate "ami:connectsTo"


 *  DO associate the noun "system" ONLY with instances of type "ami:System".  In other
    words, DO NOT consider the word "system" in other places especially names, labels,
    and comments to suggest it is an "ami:System."

 *  DO interpret the noun "architecture" to mean the recursive component dependencies,
    both up and down, for a particular system.
    

 *  DO associate the phrase "responsible for" with "ami:owner".
    Example: "Who is responsible for XYZ?" means "tell me the ami:owner of XYZ".

 *  DO associate the verb "manages" with "ami:owner" if "ami:owner" is known; otherwise,
    associate it with "ami:steward".
    Example: "Who manages XYZ?" means "tell me the ami:owner of XYZ".    


 *  DO associate the noun "complexity" in the context of software with the number of
    parent and/or child dependencies as recursively discovered via the "ami:linksWith"
    predicate.
 *  DO associate the noun "complexity" in the context of hardware with the number of
    parent and/or child dependencies as recursively discovered via the "ami:connectsTo"
    predicate.
 *  DO associate the noun "complexity" in the context of data and data shape with the
    depth of nested structures and arrays

 *  Unless otherwise instructed, ALWAYS provide
    the first and last name and DID of an Actor instead of the Actor subject URI.
    For example, to show owner of ex:system_001, DO NOT just create the SPARQL clause
        ex:system_001  ami:owner  ?owner
    but rather
        ex:system_001  ami:owner  ?owner
        ?owner ami:lastname ?ownerLastName ;
   	       ami:DID ?ownerDID .

 *  DO perform recursive transitive closure on dependencies when asked for dependents
    or complexity i.e. do not give just the first-level dependencies; walk the
    "linksWith" or "connectsTo" values to produce a graph.

 *  ASSUME that the noun "MEP" means "message exchange pattern".  MEPs appear in
    the "ami:listensFor" complex property of the "ami:Component" class.

 *  ASSUME that the noun "catalog" means the complete set of data 
 *  ASSUME that unbounded questions like "How many vendors are there?" implies the complete set of data

 *  ASSUME that "today's date" or "current date" is %s 

    
""" % ( str(datetime.datetime.now())) }

    ,{"lbl":"Common Associations", "txt":"""
Here are some common associations of nouns and verbs to the actual AMI entities.

 *  python, java, C, C++, rust, groovy, assembler, perl, shell script are all "ami:Software" 
 *  mongodb, mongo, oracle, postgres, SQLServer, DB2, MySQL, Neo4J are all databases
 *  kafka, rabbit are all message busses
 *  any "ami:Shape" definition that contains a predicate 'ex:sensitivity' is sensitive data
    
    
"""}

            
    ,{"lbl":"Snippets", "txt":"""
Snippets are query fragments that can be composed together to form
a full, valid SPARQL query.  The format of a snippet is one or terse textual
expressions followed by a SPARQL fragment wrapped with triple quotes to make it
easier for you to identify the boundaries.  Consider this snippet:

what software is Java
what software depends on Java
what depends on Java
```    
?sw  a  ami:Software ;
     ami:version [ ami:bintype "jar" ] ;
```

This means if you determine that a question has the essence of 
"getting all Java" in it then you can use the SPARQL fragment
inside the triple quotes as part of the final SPARQL query.  If the question
was
    "Fetch all java software then group by the owner and show me owner and total."
then your answer would be:
    SELECT ?owner (COUNT(?software) AS ?total)
        WHERE {
        ?software a ami:Software ;
                  ami:version [ ami:bintype "jar" ] ;
                  ami:owner ?owner .
        }
    GROUP BY ?owner

    
"""}

    ,{"lbl":"Cookbook", "txt":"""
The Cookbook contains more complex SPARQL queries called recipies.
It is similar to snippets except the entire SPARQL query is provided.
The format of a recipie is one or terse textual
expressions followed by a SPARQL statement wrapped with triple quotes to make it
easier for you to identify the boundaries.
Assume that most questions will require you to adapt the recipe to return
more or less information.

get recursive dependencies of a system
```    
SELECT DISTINCT ?start ?end
WHERE {
  ex:system_001  ami:components  ?components .
  
  {  
    ?components ami:connectsTo ?end .
    BIND(?components AS ?start)
  } UNION {
    ?start ami:connectsTo ?end . 
    ?components ami:connectsTo+ ?start .
  }
}
```    

get all software that depends on a given piece of software
get all upstream dependencies of a given piece of software
```
SELECT DISTINCT ?start ?end
WHERE {
  # Bind variable ?sw to the target piece of software
    
  {
    ?start ami:linksWith ?sw .
    BIND(?sw AS ?end)
 }
 UNION
 {
    ?start ami:linksWith ?intermediate .
    ?intermediate ami:linksWith+ ?sw .
    BIND(?intermediate AS ?end)
 }
    
}
```

find all shapes that contain sensitive data
```
SELECT DISTINCT ?shape
WHERE {
    # Step 1: Get ex:sensitivity from any triple, if it exists:
    ?sensitiveProperty sh:path ?path ;
                       ex:sensitivity ?sensitivityValue .
    
    #  FILTER by desired level of sensitivity.
    #  ADJUST THIS AS NEEDED:
    FILTER(?sensitivityValue > 1 && ?sensitivityValue < 4)

    # Step 2: Trace back to the root shape
    ?intermediateShape (sh:property|sh:node)* ?sensitiveProperty .

    # Only pick classes that are actually top-level AMI Shape.  Note
    # that all the subfields are type sh:NodeShape but they are NOT
    # ami:Shape!
    ?shape sh:property ?intermediateShape ;
           a ami:Shape .
}
```

find all components that use shapes containing sensitive data in their MEPs
```
SELECT DISTINCT ?component ?mep ?shape
WHERE {
    # Step 1: Identify any property with ex:sensitivity > 2 and < 4
    ?sensitiveProperty sh:path ?path ;
                       ex:sensitivity ?sensitivityValue .

    #  FILTER by desired level of sensitivity.
    #  ADJUST THIS AS NEEDED:    
    FILTER(?sensitivityValue > 1 && ?sensitivityValue < 4)

    # # Step 2: Trace back to the root shape
    ?intermediateShape (sh:property|sh:node)* ?sensitiveProperty .

    # Only pick classes that are actually top-level AMI Shape.  Note
    # that all the subfields are type sh:NodeShape but they are NOT
    # ami:Shape!
    ?shape sh:property ?intermediateShape ;
           a ami:Shape .

    # # Step 3: Find components related to these shapes:
    ?component ami:listensFor ?mepEntry .

    ?mepEntry ?mep ?mepShape .

    # # Check for shapeIn or shapeOut:
    {
         ?mepShape ami:shapeIn ?shape
    }
    UNION
    {
        ?mepShape ami:shapeOut ?shape
    }
}
```
    
    
    
"""}            
    
    ]


        preamble = """\
You are AMI, the Intelligent Query System.
I am a technical manager/architect.   I use AMI to turn natural language questions
like "What Software is going EOL this year?" into SPARQL queries that I 
can apply to my RDF triple store to yield an answer.  AMI does not need the actual
data; it only needs to know how to ask for it.

You will now be given %d blocks of input that describe the AMI system:
""" % len(blocks)
        for index,b in enumerate(blocks):
            preamble = preamble + "%d. %s\n" % (index+1, b['lbl'])
        preamble += "Standby to receive these blocks."

        self.conversation.predict(input=preamble)  # ignore output for

        for index,b in enumerate(blocks):
            blurb = "\nBLOCK %d: %s\n" % (index+1, b['lbl'])

            print("BLOCK %d of %d..." % (index+1,len(blocks)))
            blurb += b['txt']
            if index < len(blocks)-1:
                blurb += "\nThere is no need to respond at this moment.\nPlease prepare for the next block. "

            while True:
                retry_time = 2        
                try:
                    response = self.conversation.predict(input=blurb)  # ignore output for
                    #print(response)
                    break
                except openai.error.RateLimitError as e:
                    error_message = str(e)

                    retry_time_match = re.search(r"Please try again in (\d+(\.\d+)?)s", error_message)
                    if retry_time_match:
                        retry_time = float(retry_time_match.group(1))
                        retry_time += 1  # extra buffer
                        print("Rate limit exceeded; sleeping parsed", retry_time)
                    else:
                        print("Rate limit exceeded; no retry_after; assume", retry_time)

                    time.sleep(retry_time)   # seconds
                    continue

                except Exception as e:
                    print(f"An error occurred: {e}")
                    sys.exit(1)

        blurb = """\
You will now be asked questions about the data.

Please respond now with:
AMI System query interface ready.  Type "show me all system owners and departments" to get tarted.
"""
        self.ask(blurb, False) 


    def collect_input(self):
        inputs = []
        while True:
            # Print the prompt without a newline and flush to ensure it displays immediately
            if self.fd is None:
                user_input = input("> ")
            else:
                user_input = self.fd.readline()

#                print("[%s]" % user_input)
                
                if user_input == "":  # EOF
                    if self.rargs.keepgoing is True:
                        self.fd = None
                        inputs = []                        
                        continue
                    else:
                        break

                if user_input[0:1] == '#':
                    continue
                else:
                    user_input = user_input.rstrip()                
                    print("[%s]" % user_input)
                
            # Check if the input is empty
            if user_input == "" :
                break
        
            # Append the input to the list
            inputs.append(user_input)
    
        return inputs



    def go(self):
        self.init_system()

        while True:
            collected_inputs = self.collect_input()
            if 0 == len(collected_inputs):
                break
            self.ask(" ".join(collected_inputs), False)

            
def main():
    parser = argparse.ArgumentParser(description=
"""AMI2 query interface.
"""
   )

    parser.add_argument('--model', 
                        metavar='OpenAI model to use',
                        default='gpt-3.5-turbo')

    parser.add_argument('--keepgoing',
                        action='store_true',
                        help='Only used if script is supplied.  If set, program will not exit after script is read but instead will switch to stdin for input')

    parser.add_argument('script',
                        nargs='?')
                        
    rargs = parser.parse_args()

    print(rargs)
    
    #  Get this out of way before banging on the API...
    fd = None
    if rargs.script is not None:
        try:
            fd = open(rargs.script, "r")
        except:
            print("error: cannot open", rargs.script)
            return
    
    key_var = 'OPENAI_API_KEY'
    if key_var not in os.environ:
        print("error: set", key_var)
        return
    
    API = os.environ[key_var]

    #temp = 0.2   # between 0 and 2, default is 1.  .2 is more focused, .8 more random
    temp = 0  # as conservative as possible...
    #mname = "gpt-4"

    # max_retries = 0 to let RateLimitError percolate back to us...
    llm = ChatOpenAI(model_name=rargs.model, temperature=temp, max_retries=0, openai_api_key=API)

    memory = ConversationBufferMemory()
    conversation = ConversationChain(llm=llm, memory=memory)

    p = Program(conversation, fd, rargs)
                
    p.go()

if __name__ == "__main__":        
    main()
        


#    Retrying langchain.chat_models.openai.ChatOpenAI.completion_with_retry.<locals>._completion_with_retry in 8.0 seconds as it raised RateLimitError: Rate limit reached for gpt-4 in organization org-nvMKUS0EwCBGwqBt8agwJj9m on tokens per min (TPM): Limit 10000, Used 8339, Requested 7835. Please try again in 37.044s. Visit https://platform.openai.com/account/rate-limits to learn more..

