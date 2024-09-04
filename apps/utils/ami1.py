
from langchain.chat_models import ChatOpenAI
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

#  https://github.com/microsoft/azurechatgpt
#  https://news.ycombinator.com/item?id=37112741


key_var = 'OPENAI_API_KEY'
if key_var not in os.environ:
    print("error: set", key_var)

API = os.environ[key_var]

#temp = 0.2   # between 0 and 2, default is 1.  .2 is more focused, .8 more random
temp = 0  # as conservative as possible...
#mname = "gpt-4"
mname = 'gpt-3.5-turbo'

# max_retries = 0 to let RateLimitError percolate back to us...
llm = ChatOpenAI(model_name=mname, temperature=temp, max_retries=0, openai_api_key=API)
#llm = ChatOpenAI( temperature=temp, openai_api_key=API)    

memory = ConversationBufferMemory()

conversation = ConversationChain(llm=llm, memory=memory)


def ask(blurb,echo=True):
    if echo is True:
        print("ME:", blurb)
    xx = conversation.predict(input=blurb)
    #print("ChatGPT:", xx)
    print(xx)
    print()


ami_meta_f = "/Users/buzz/git/AMI/ami.ttl"
with open(ami_meta_f) as fd:
    ami_meta = fd.read()

ami_data_f = "/Users/buzz/git/AMI/data.ttl"
with open(ami_data_f) as fd:
    ami_data = fd.read()    


print("Initializing system with model %s ..." % mname)

blocks = [
    {"lbl":"Overall Design", "txt":"""
This an overall design summary of the AMI System:
 *  AMI is based on RDF triples

 *  The main classes are Software, Hardware, Shape, Component, and System.  The main
    classes derive from class Item which provides foundational properties such as
    owner, steward, creation time, etc.  

 *  Software has a property "linksWith" whose value is another Software instance.
    This is how recursive dependencies can be constructed.

 *  Components define interfaces and declare their dependencies with the
    "connectsTo" property whose value is another Component.  This is how a multi
    component system can be built.

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


    ,{"lbl":"AMI Data", "txt":"""
Below are instances of `ami:` classes and properties in RDF turtle format that declare actual
instances of software and hardware and components and the relationships
between them.
This system's actual instances are placed in the `ex:` prefix namespace.

The data RDF ends when you see the line `# END DATA`.

%s

# END DATA
""" % ami_data}

    ,{"lbl":"Assumptions and Instructions", "txt":"""
Here are important assumptions and instructions:
 *  DO NOT echo acknowledgement of the metadata or data.
 *  DO NOT append friendly "if you have more questions..." verbiage to your answers.

 *  When asked to show, list, or otherwise fetch "items", ALWAYS fetch ALL
    instances of type "ami:Item" which implies any classes derived from Item such
    as "ami:Software" and "ami:Hardware", and then filter down if appropriate.
    
 *  When asked to show, list, or otherwise fetch "software", ALWAYS fetch ALL
    instances of type "ami:Software", and then filter down if appropriate.

 *  DO associate the noun "hardware" with any instance that is of type "ami:Hardware"
 *  DO associate the phrase "depends on" in the context of software with the predicate "ami:linksWith"
 *  DO associate the phrase "depends on" in the context of components with the predicate "ami:connectsTo"


 *  DO associate the noun "system" ONLY with instances of type "ami:System".  In other
    words, DO NOT consider the word "system" in other places especially names, labels,
    and comments to suggest it is an "ami:System."
 *  DO interpret the noun "architecture" to mean the recursive component dependencies,
    both up and down, for a particular system.
    

 *  DO rely on the "rdfs:label" property, if it exists, to provide a general identifier
    of a thing (software, hardware, component, etc.) without getting into details of
    version.  For example, you will get questions like "Where do we use log4j?"; you
    can use the "rdfs:label" property as a "tag" to help you narrow your response.

 *  DO rely on the "rdfs:comment" property, if it exists, to provide very accurate
    textual detail of a entity, which will help you build better responses.

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

 *  If your response to a question includes an "ami:Actor" instance, ALWAYS provide
    the first and last name and DID of the Actor instead of the Actor subject.  For
    example, DO NOT say "is managed by actor with ID B87" but instead say
    "is managed by Jane Doe ID B87".

 *  DO expect to be asked to provide a SPARQL query for any textual response you provide.
 *  ABSOLUTELY DO NOT invent RDF predicates in your SPARQL responses.  All predicates MUST come from
    the supplied 'ami:' or 'sh:' prefixes.  If you cannot do so, you must ask for
    more information.
 *  DO NOT prompt me to create a SPARQL query after each question; just be prepared
    to reinforce your textual answer.

 *  DO perform recursive transitive closure on dependencies when asked for dependents
    or complexity i.e. do not give just the first-level dependencies; walk the
    "linksWith" or "connectsTo" values to produce a graph.


 *  ASSUME that "today's date" is %s
 *  ASSUME that the noun "catalog" means the complete set of data
 *  ASSUME that unbounded questions like "How many vendors are there?" implies the complete set of data

 *  If an "ami:Shape" instance has no owner or steward, you WILL assume the shape 
    owner and steward are both the steward of the Component that names the shape in
    one of its message exchange patterns.

""" % ( str(datetime.datetime.now())) }

    ]


preamble = """\
You are AMI, the Asset Management and Intelligence System.
I am a technical manager/architect.   I use AMI to learn about what is in my
technology footprint.

You will now be given %d blocks of input that describe the AMI system:
""" % len(blocks)
for index,b in enumerate(blocks):
    preamble = preamble + "%d. %s\n" % (index+1, b['lbl'])
preamble += "Standby to receive these blocks."

conversation.predict(input=preamble)  # ignore output for
#ask(preamble, False) 

for index,b in enumerate(blocks):
    blurb = "\nBLOCK %d: %s\n" % (index+1, b['lbl'])
    print("BLOCK %d of %d..." % (index+1,len(blocks)))
    blurb += b['txt']
    if index < len(blocks)-1:
        blurb += "\nThere is no need to respond at this moment.\nPlease prepare for the next block. "

    while True:
        retry_time = 2        
        try:
            response = conversation.predict(input=blurb)  # ignore output for
            print(response)
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
            # Optionally, implement a retry mechanism here if desired
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)





blurb = """\
You will now be asked questions about the data.
Please respond now with "AMI System query interface ready.
"""
ask(blurb, False) 


def collect_input():
    inputs = []
    while True:
        # Print the prompt without a newline and flush to ensure it displays immediately
        user_input = input("> ")
        
        # Check if the input is empty
        if user_input == "":
            break
        
        # Append the input to the list
        inputs.append(user_input)
    
    return inputs

while True:
    collected_inputs = collect_input()
    if 0 == len(collected_inputs):
        break
    ask(" ".join(collected_inputs), False)



#    Retrying langchain.chat_models.openai.ChatOpenAI.completion_with_retry.<locals>._completion_with_retry in 8.0 seconds as it raised RateLimitError: Rate limit reached for gpt-4 in organization org-nvMKUS0EwCBGwqBt8agwJj9m on tokens per min (TPM): Limit 10000, Used 8339, Requested 7835. Please try again in 37.044s. Visit https://platform.openai.com/account/rate-limits to learn more..

