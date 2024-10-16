
from langchain_openai import ChatOpenAI

from langchain.chains import LLMChain, ConversationChain
from langchain.memory import ConversationBufferMemory

import openai

import requests

import datetime
import time
import json
import os
import re
import sys
import argparse

class AMI():
    
    def init_llm(self):
        #temp = 0.2   # between 0 and 2, default is 1.  .2 is more focused, .8 more random
        temp = 0  # as conservative as possible...
        #mname = "gpt-4"

        # max_retries = 0 to let RateLimitError percolate back to us...
        llm = ChatOpenAI(model_name=self.model, temperature=temp, max_retries=0, openai_api_key=self.api_key)
        memory = ConversationBufferMemory()

        conv = ConversationChain(llm=llm, memory=memory)

        conv.predict(input="ASSUME todays date and current date are %s." % str(datetime.datetime.now()))
                
        return conv
    
    def __init__(self, **kwargs):
        self.api_key = kwargs.get('api_key')
        if None == self.api_key:
            raise Exception("error: must provide api_key")

        self.ami_cpt_f = kwargs.get('ami_cpt')
        if None == self.ami_cpt_f:
            self.ami_cpt_f = "ami.cpt"

        self.local_cpt_f = kwargs.get('local_cpt')
        if None == self.local_cpt_f:
            self.local_cpt_f = "local.cpt"

        self.snippet_f = kwargs.get('snippets')
        if None == self.snippet_f:
            self.snippet_f = "snippets.txt"                        

            
        self.model = 'gpt-4o-mini'

        self.ami_conversation = self.init_llm()
        self.general_conversation = self.init_llm()        

        self.init_system()
        

    def askAMI(self, blurb,echo=False):
        if echo is True:
            print("ME:", blurb)
        xx = ""
        try:
            xx = self.ami_conversation.predict(input=blurb)
        except Exception as e:
            xx = "AMI LLM error: " + str(e)
        return xx

    def askGeneral(self, blurb,echo=False):
        if echo is True:
            print("ME:", blurb)
        xx = ""
        try:            
            xx = self.general_conversation.predict(input=blurb)
        except Exception as e:
            xx = "General LLM error: " + str(e)
        return xx    
        

    def init_system(self):
        with open(self.ami_cpt_f) as fd:
            ami_cpt = fd.read()

        with open(self.local_cpt_f) as fd:
            local_cpt = fd.read()            
            
        print("Initializing system with model %s ..." % self.model)

        blocks = [
    {"lbl":"Overall Design", "txt":"""
This an overall design summary of the AMI System:
 *  AMI is based on RDF triples

 *  The main classes are Software, Hardware, Shape, Component, System, and Report.

 *  An IMPORTANT feature of AMI is how data definitions (Shape) are brought
    together with software and hardware to present a complete view of what
    a system of components is trying to do.

 *  Software has a property "linksWith" whose value is another Software instance.
    This is how recursive dependencies can be constructed.  Multiple "linksWith"
    properties are of course supported.

 *  Components define interfaces and declare their dependencies with the
    "connectsTo" property whose value is another Component.  This is how a multi
    component system can be built.  

 *  A critical feature is that Components have a property "entryPoint"
    whose value is a Software.  This is what binds an abstract definition of a system
    to the actual code that runs it.  See "entryPoint" property definition for
    more detail.

 *  A System is a named administrative "starting point" for a cooperating collection of
    Components e.g. the "Vacation Tracking System."  A System does not have to name
    all the components.  Typically, the "top-most" GUI application component is named
    and dependent components can be derived from the "connectsTo" property.  Systems
    are how the business and a technical manager view and organize technology.

 *  A Report is a saved SPARQL query.
    """}


    ,{"lbl":"AMI Metadata", "txt":"""
Below is a set of subject-predicate-object triples that is the metadata for
the AMI system.

The triples are in prefixed bar-delimited format.
Object literals are wrapped with double quotes and optionally cast to the
appropriate XSD datatype if they are not plain strings; otherwise, object URIs
are unquoted.  Examples:
object URI:             ami:swtype|rdfs:range|xsd:string
object literal string:  ami:swtype|rdfs:label|"software type"
object literal int:     ami:swtype|ami:maxvers|"10"^^xsd:int

Here are the prefix mappings expressed in turtle format:

@prefix ami: <http://moschetti.org/ami#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    
You should use the rdfs:label and rdfs:comment triples to help you associate
questions with specific properties.  From there, you can use the rdfs:domain
predicate to get the containing class, which itself may have an instance as a
Property in another containing class.  Example:  Suppose the question is:

    Find all software with binary type of 'jar' 

Here are the steps you can take to build the desired SPARQL output:
1.  There is a strong match to a triple in the dataset like this:
    ami:bintype|rdfs:comment|\"x86_64\" and \"jar\" are two common binary file types.  Note that \"python\" is also a valid type even though technically it is not binary.
2.  ami:bintype is indeed a Property:
        ami:bintype|rdf:type|rdf:Property
3.  The containing class is ami:Version:
        ami:bintype|rdfs:domain|ami:Version
4.  ami:Version is the rdfs:range i.e. the class type of ami:version
5.  ami:version is a Property:
        ami:version|rdf:type|rdf:Property
6.  ami:version is contained in classes Software, Hardware, and Shape:
        ami:version|rdfs:domain|ami:Shape
        ami:version|rdfs:domain|ami:Hardware
        ami:version|rdfs:domain|ami:Software

Thus, the appropriate SPARQL fragment would be:

    ?software a  ami:Software ;
              ami:version  ?vv .
    ?vv ami:bintype "jar" .

The metadata ends when you see the line `# END METADATA` and this
line is not part of the metadata.

%s
# END METADATA
"""  % ami_cpt}


            
    ,{"lbl":"Local Metadata", "txt":"""
Below is a set of subject-predicate-object triples that is the local
extension to the AMI system.
The triple are in prefixed bar-delimited format.

The metadata ends when you see the line `# END METADATA` and this
line is not part of the metadata.

%s

# END METADATA
"""  % local_cpt}            

    ,{"lbl":"SPARQL Assumptions and Instructions", "txt":"""
The following instructions apply ONLY when you decide to generate SPARQL
instead of responding in a textual fashion.

 *  The output variable names of your generated SPARQL queries MUST be simple
    mixed case alpha ONLY; NO whitespace or special characters permitted.

 *  ALWAYS create a response that has 3 parts and ONLY these 3 parts:
    1.  It is VERY IMPORTANT to create a first line exactly like this:
        ## SPARQL
        Note the double hash characters.  This is a "signature" line that
        is IMPORTANT for signalling consumers of your output.
    
    2.  Textual insightful narrative about how you created the SPARQL statement
        including notes on how you interpreted the question.
        The narrative will be lines of text no longer than 60 characters.
        EVERY narrative line is preceded with the hash (#) character which is the
        SPARQL comment character.
        You MUST include at LEAST one line but more detail on more lines is
        encouraged.
    
    3.  The SPARQL query itself.

    For example, when asked:
        Please group the assets by manager and print a list of manager and
        total number of assets for that manager only if the total is greater
        than 2, and sort by total
    your response should be similar to this:
        ## SPARQL
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

    NEVER add narrative after the SPARQL query.
    
 *  DO NOT use the clause `?item a ami:Item` in the construction of any query.

 *  NEVER invent RDF predicates in your SPARQL responses.
    All predicates MUST come from the supplied 'ami:','sh:', 'exc:', or
    'exr:' prefixes.  If you cannot do so, you must respond <CANNOT_ANSWER>

 *  ASSUME that specific instance subjects and objects that you may use in your
    construction of SPARQL are in the 'dd:' namespace.
    For example to find properties of system 'system_001':
        SELECT *
        WHERE {
            dd:system_001 a ami:System .
        }
    
 *  Colon-prefixed identifiers e.g. 'dd:myApp' and 'ami:EOL' and 'dd:lib3'
    ARE ALWAYS URIs, not literal strings.  For example, given the
    following question:
        Show rdfs:comment for all Shapes
    means use the specific property 'rdfs:comment' as part of your SPARQL
    construction.
    
 *  ASSUME that quoted strings mean URIs, not literal strings or
    unbound variables.  For example, given the following question:
        Show everything that depends on software "lib77"
    it should be interpreted as 
        Show everything that depends on software instance dd:lib77    

 *  ASSUME that unquoted identifiers entities MIGHT imply URIs, not
    literal strings or unbound variables.  For example, given the following question:
        Show everything that depends on software lib77
    it should be interpreted as 
        Show everything that depends on software instance dd:lib77

    
 *  ALWAYS RELY on the 'rdfs:label' property as a general terse descriptor
    of a software, hardware, component, or system instance.  All instances
    will ALWAYS have an 'rdfs:label' property.

 *  DO RELY on the 'rdfs:comment' property to provide very
    accurate textual detail of a entity, which will help you associate the
    question with the correct properties and classes to use in
    the SPARQL statement.

 *  BEWARE that unlike `rdfs:label`, 'rdfs:comment' is not mandatory;
    thus, when filtering on *other* properties and you
    add 'rdfs:comment' to the output, ALWAYS make sure `rdfs:comment`
    is OPTIONAL.  For example, if the question is "List all Actors",
    you can safely include `rdfs:label` but make `rdfs:comment`
    OPTIONAL because we do not want to restrict the output if the
    `rdfs:comment` is not set:
    ```
        SELECT *
        WHERE {
            ?actor a ami:Actor ;
                   rdfs:label ?label .
            OPTIONAL { ?actor rdfs:comment ?comment  . }
        }
    ```
   
 *  ALWAYS use the 'rdfs:comment' property when presented with very broad
    questions like:
        "What software is used for risk?"
        "Show me everything that makes graphics"
        "What systems are used for machine parts inventory management?"
    
    Improve your chances of a match by canonicalizing 'rdfs:comment' to
    lowercase as follows (assuming ?comment is bound to 'rdfs:comment'):
        FILTER(CONTAINS(LCASE(?comment), "keyword"))

    The hope is that the owner of the property will have made it descriptive
    enough to include one or more good keywords.
    
 *  DO associate the noun "asset" with any of type 'ami:Software',
    'ami:Hardware', 'ami:Shape' , 'ami:Component', or 'ami:System'
    
 *  ALWAYS associate the noun "software" in a question with type "ami:Software"
 *  ALWAYS associate the noun "hardware" in a question with type "ami:Hardware"
    
 *  ALWAYS associate the phrase "depends on" in the context of software with the predicate "ami:linksWith"
 *  ALWAYS associate the phrase "depends on" in the context of components with the predicate "ami:connectsTo"


 *  DO interpret the noun "architecture" to mean the recursive component
    dependencies, both up and down, for a particular system.
    
 *  DO associate the phrase "responsible for" with BOTH properties 'ami:owner'
    and 'ami:steward'.  Example:
        "Who is responsible for XYZ?"
    means
        "Tell me the ami:owner name and ami:steward name of XYZ".

 *  DO associate the terms "manages" with BOTH properties 'ami:owner'
    and 'ami:steward'.  Example:
        "Who manages component ABC?"
    means
        "Tell me the ami:owner name and ami:steward name of XYZ".    


 *  "Complexity" in the context of software is the number of
    parent and/or child dependencies as recursively discovered via the
    'ami:linksWith' predicate.
    
 *  "Complexity" in the context of components is the number of
    parent and/or child dependencies as recursively discovered via the
    'ami:connectsTo' predicate.
    
 *  "Complexity in the context of data shapes is the
    depth of nested structures and arrays

 *  DO NOT return an 'ami:Actor' instance in query.  If an 'ami:Actor' instance
    becomes a terminal variable in a query, ALWAYS go one step further and
    extract the 'rdfs:label' for the name.  Example:
        dd:system_001  ami:owner  ?owner  # do not stop here...
        ?owner rdfs:label ?name .         # much more useful return

 *  ALWAYS use the 'rdfs:label' when asked for owner name or steward name.
    For example, to show owner of 'dd:system_001', DO NOT just create the
    SPARQL clause
        dd:system_001  ami:owner  ?owner
    but rather
        dd:system_001  ami:owner  ?owner
        ?owner rdfs:label ?name .

 *  ASSUME that the noun "catalog" means the complete set of data 

""" }

    ,{"lbl":"Special handling of AMI Shapes", "txt":"""
The following instructions apply when you are asked these specific
questions about Shapes:

 *  If a request is made to see the definition of shape (which might
    involve nested structures), you will respond simply with
        ## SHAPE DETAIL <id1> <id2> ...
    where <idn> is a shape entity IDs.  The context of the conversation
    may involve more than one shape, hence the need for a variable length list.
    For example, consider this Shape
    declaration (boilerplate properties like rdfs:label omitted for clarity):
    ```
    dd:coll1 a sh:NodeShape, ami:Shape ;
    sh:property [
        sh:path dd:id ;
        sh:datatype xsd:string ;
    ] ;
    sh:property [
        sh:path dd:updated ;
        sh:datatype xsd:dateTime ;
    ] .
    ```
    If asked "Show me the detail of shape dd:coll1." you will respond with:
        ## SHAPE DETAIL dd:coll1    

    Here is a more complicated example:
    Input: "Show me all shapes where owner name is Bob"
    Your output:  A SPARQL query that produces, for example, 3 shapes.
    Input: "Show me the detail for these shapes"
    Your output:  ## SHAPE DETAIL dd:shape1 dd:shape2 dd:shape3
    
 *  If a request is made to see a sample representation of a shape,
    you will respond simply with
        ## SHAPE SAMPLE <id1> <id2> ...
    For example, using the Shape declaration above, 
    if asked "Show me a sample or example of shape dd:coll1" 
    you will respond with
        ## SHAPE SAMPLE dd:coll1 
""" }
            
    ,{"lbl":"Common Associations", "txt":"""
Here are some common associations of nouns and verbs to the actual AMI entities.
Some of these will reinforce definitions in the AMI metadata itself, particularly
in the "rdfs:comment" property.
    
 *  python, java, C, C++, rust, groovy, assembler, perl, shell script are all "ami:Software" 
    
 *  mongodb, mongo, oracle, postgres, SQLServer, DB2, MySQL, Neo4J are all databases

 *  iOS, android are platforms
    
 *  kafka, rabbit are all message busses
    
 *  python, jar, war, x86_32, x86_64, arm64 are all binary file types.
    
 * "app", "service", "daemon", and "lib" are common Software ami:swtypes.
   "app" a.k.a. application means something that a users sees and interacts with.

 * "service" and "daemon" mean something that is started by automated processes and
   continues to run "in the background", waiting to perform tasks, typically for
   applications but certainly also for other services.
    
 * Databases, web services, and message busses are specialized examples of services.

 *  "Vulnerability" is a weakness or gap in protection; "Risk" is the likelihood
    of exploitation of the vulnerability.

 * "lib" a.k.a. library is releasable unit of code like log4j-core-2.17.1.jar.

    
"""}
    
    ]

        #blocks = []  # HA HA
        
        preamble = """\
You are AMI, the Asset Management and Intelligence System.

I am a manager of technology and will ask you questions in
a conversational manner.   

You will use your knowledge of SPARQL, AMI metadata, and local metadata to
answer my questions in one and ONLY ONE of these four ways:
        
1.  Produce SPARQL queries that when applied to a triple store would
    yield the appropriate data.  There are rules and assumptions for
    your construction of SPARQL queries that will be covered shortly.
    Example:
        My input:  "Please list all systems in AMI."
        Your output:  A SPARQL query

    Note that because of your knowledge of the metadata, you can produce
    SPARQL queries that will precisely return information about yourself:
        My input:  "What are all the properties of the Sofware class?"
        Your output:  A SPARQL query similar to this:
        ## SPARQL
        # This query retrieves all properties associated with the Software class.
        # It lists the properties along with their labels and comments for better understanding.
        SELECT ?property ?label ?comment
        WHERE {
          ?property rdfs:domain ami:Software .
          OPTIONAL { ?property rdfs:label ?label . }
          OPTIONAL { ?property rdfs:comment ?comment . }
        }        

        
2.  Answer general questions about yourself and your metadata.  This will not require you to
    generate SPARQL but instead a more traditional textual response.  Examples:

    My input:  "What can you do?" or "Tell me about yourself" or "What is AMI?"      
    Your output:  "I can answers questions about the software, components, data,
        and other entities stored in the backing CMDB."

    My input:  "Tell me about AMI Components and their relationship to Software."
    Your output:  "AMI Components are an abstract description of a service that interacts with other components according to various message exchange patterns. They define interfaces and declare their dependencies using the "connectsTo" property, which specifies other components they require to function. ...."

    It is IMPORTANT to recognize that any mention of "AMI" means you, NOT
        other popular acronyms such as Advanced Metering Infrastructure or
        AI Messenger.

3.  Answer questions about AMI Shapes.  Shape definitions in AMI subscribe
    to an industry standard called SHACL but this format is not particularly
    consumable by a user.  Therefore, when asked about shapes, special rules
    will apply that will be covered shortly.

4.  A VERY IMPORTANT instruction is that if you cannot answer a question in
    style 1, 2, or 3 above, YOU MUST respond with the
    EXACT phrase <CANNOT_ANSWER> including the angle brackets. This is VITAL
    as a signal to a consumer.
        
Your responses should be professional and terse.        

You will now be given %d blocks of input that describe you, the AMI system:
""" % (len(blocks))

        if len(blocks) > 0:
            for index,b in enumerate(blocks):
                preamble = preamble + "%d. %s\n" % (index+1, b['lbl'])
            preamble += "Standby to receive these blocks."

            self.askAMI(preamble)

        else:
            print("* not loading preamble or blocks")

        for index,b in enumerate(blocks):
            blurb = "\nBLOCK %d: %s\n" % (index+1, b['lbl'])

            print("BLOCK %d of %d..." % (index+1,len(blocks)))
            blurb += b['txt']
            if index < len(blocks)-1:
                blurb += "\nThere is no need to respond at this moment.\nPlease prepare for the next block. "

            while True:
                retry_time = 2        
                try:
                    response = self.askAMI(blurb)  # ignore output for
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
I will now provide you with SPARQL snippets.
A SPARQL snippet is a bullet list of brief descriptions of a goal or pattern,
followed by explanatory narrative, then followed by a SPARQL statement that
achieves the goal.  You can use snippets to help you construct better responses
for SPARQL generation.  

Some snippets contain more than one goal-SPARQL because the
context is similar and therefore useful for you to interpret as a whole.
Snippets with more than one goal-SPARQL will have a common theme that will
reinforce certain common SPARQL design features.
Goal-SPARQL are separated by a line starting with "----" for extra clarity.

Note that example URIs and strings like "ex:exampleInstance" and
"exampleSoftwareName" are "placeholders" and will ALWAYS have to be substituted
with the appropriate URIs and strings for the particular query.
        
You WILL need to adapt the snippet to return the appropriate information in the context
of the input question especially with respect to variable names and grouping.  

        
"""
        self.askAMI(blurb)

        nr = 0

        def mksnippet(n,lines):
            stxt = """
AMI Snippet #%d

%s

Remember this snippet.
""" % (n,  ''.join(recipe_lines).strip())
            return stxt

                        
        with open(self.snippet_f, 'r') as file:
            recipe_lines = []
            for line in file:
                # If we hit the separator, process the current recipe
                if line.strip() == '====':
                    # If recipe_lines has content, call foo with the accumulated recipe text
                    if recipe_lines:
                        nr += 1
                        recipe_text = mksnippet(nr,recipe_lines)
                        print(self.askAMI(recipe_text))
                        recipe_lines = []  # Reset for the next recipe
                else:
                    # Accumulate lines if not a separator
                    recipe_lines.append(line)

            # After the loop, handle the last recipe if it exists
            if recipe_lines:
                nr += 1
                recipe_text = mksnippet(nr,recipe_lines)                
                print(self.askAMI(recipe_text))

        
        blurb = """\
You and I will now settle into a question and answer session.

Please respond now with the following text, maintaining the newlines:
        
AMI System query interface ready.  Here are some starter suggestions for questions you can ask me:
1.  Show me all system descriptions, owner names, and departments
2.  Tell me about all my vendors.
3.  What software is going EOL in the next 2 years?
4.  Please group assets by owner name and show me the totals.
"""
        print(self.askAMI(blurb))



def emitResponse(cr_delimited_string):
    # Split the input into lines and filter out blank lines
    lines = [line for line in cr_delimited_string.splitlines() if line.strip()]
    
    # Parse the first non-blank line to check the status and get the 'vars' array
    first_line = json.loads(lines[0])
    if first_line.get('status') != 'OK':
        print(first_line)
        return

    # Get the 'vars' array and print it in a bar-delimited form
    vars_list = first_line.get('vars', [])
    print('|'.join(vars_list))
    
    # Process each subsequent line
    for line in lines[1:]:
        parsed_line = json.loads(line)

        # Collect values for each var in the vars_list, use empty string if the key doesn't exist
        values = [str(parsed_line.get(var, "")) for var in vars_list]
        
        # Emit the bar-delimited string
        print('|'.join(values))

        
def collect_input():
    inputs = []
    while True:
        # Print the prompt without a newline and flush to ensure it displays immediately
        if None == None:  # TBD TBD
            user_input = input("> ")
        else:
            user_input = self.fd.readline()
            
            if user_input == "":  # EOF
                break
                
            if user_input[0:1] == '#':
                continue
            else:
                user_input = user_input.rstrip()                
                    
        # Check if the input is empty
        if user_input == "" :
            break
                    
        # Append the input to the list
        inputs.append(user_input)
                    
    return inputs


    
def main():
    parser = argparse.ArgumentParser(description=
"""AMI query interface.
"""
   )

    parser.add_argument('--api_key', 
                        metavar='OpenAI API key')
    
    parser.add_argument('--ami_cpt', 
                        metavar='Filename containing core AMI metadata')

    parser.add_argument('--local_cpt', 
                        metavar='Filename containing AMI extensions metadata')

    parser.add_argument('--snippets', 
                        metavar='Filename containing SPARQL snippets')    
    
    rargs = parser.parse_args()

    
    aa = AMI(api_key=rargs.api_key, ami_cpt=rargs.ami_cpt, local_cpt=rargs.local_cpt, snippets=rargs.snippets)
    
    nn = 0
    while True:
        collected_inputs = collect_input()
        if 0 == len(collected_inputs):
            break

        qq = " ".join(collected_inputs)
            
        if qq[0] == '!':
            print(aa.askGeneral(qq))
            continue

        candidate = aa.askAMI(qq)

        url = 'http://localhost:5656/sparql'
        headers = {
            'Content-Type': 'application/sparql-query',  # or 'application/x-www-form-urlencoded'
            'Accept': 'application/json'  # Expecting JSON results
        }
        
        if candidate == "<CANNOT_ANSWER>":
            print("** AMI cannot answer; asking global")
            print(aa.askGeneral(qq))

        else:
            print(candidate)

            #  TBD: Need better way to separate SPARQL output from valid AMI output...
            if "## SPARQL" in candidate:
                print("** calling jenaserver...")

                response = requests.post(url, data=candidate, headers=headers)
                #print("code", response.status_code)

                #print("JSRV", response.json())
                    
                response_data = response.text                
                emitResponse(response_data)                
                    
                qq = input("Stash this output (n [default]/y)? ");

                if len(qq) == 0:
                    qq = 'n'

                if qq.lower() == 'y':
                    nnt = """
                    I used the following SPARQL query to collect data about my technology assets:
                    %s
                    This is the output in bar-delimited table format.  The first line
                    is the header line, followed by rows of data:
                    %s
                    Add this information to our dialogue as dataset %d; we will refer to it later.
                    Please respond in brief.                    
                    """ % (candidate, response_data, nn)
                    nn += 1
                    
                    print(aa.askGeneral(nnt))
                else:
                    print("ok; not stashing.")


                        
if __name__ == "__main__":        
    main()
        


#    Retrying langchain.chat_models.openai.ChatOpenAI.completion_with_retry.<locals>._completion_with_retry in 8.0 seconds as it raised RateLimitError: Rate limit reached for gpt-4 in organization org-nvMKUS0EwCBGwqBt8agwJj9m on tokens per min (TPM): Limit 10000, Used 8339, Requested 7835. Please try again in 37.044s. Visit https://platform.openai.com/account/rate-limits to learn more..

