import rdflib
import json

import requests


from AMI import AMI  # Assuming your AMI class is in a module

class TestDriver:

    class dummyAMI:
        def __init__(self, api_key, ami_cpt, local_cpt, snippets):
            pass

        def askAMI(self, test_query):
            return "<CANNOT_ANSWER>"
            
            return """## SPARQL
#
select * WHERE {
            ?s a ami:Vendor .
            }
            """

        def askGeneral(self, test_query):
            return("""{"computed_category":0, "narrative":"dummy"}""")

    class AMIServer:
        def __init__(self):
            pass

        def askAMI(self, test_query):
            url = 'http://localhost:5001/sparql'

            hdrs = { 'Content-Type': 'application/json' }

            data = json.dumps({"question": test_query,"systemSize": "Simple"})

            # POST returns "old" format; GET returns SPARQL 1.1. SERVICE compatible format
            response = requests.post(url, data=data, headers=hdrs)

            #print("RAW AMI RESPONSE:", response.text)
            
            narrative = "<CANNOT_ANSWER>"
            if response.status_code == 200:
                qq = response.json()
                print("AMI RESP:", qq)
                narrative = qq['narrative']
            return narrative

        def askGeneral(self, test_query):
            #print("ASK GENERAL:", test_query)
            return self.askAMI("!" + test_query)  # oooo!
    

    def __init__(self, api_key, ami_cpt, local_cpt, snippets, inputfile, outputfile):
        self.graph = rdflib.Graph()
        self.graph.parse(inputfile, format="ttl")

        n_asks = 0
        for test_case in self.graph.subjects(rdflib.RDF.type, rdflib.URIRef('http://moschetti.org/amit#Test')):
            for ask_block in self.graph.objects(test_case, rdflib.URIRef('http://moschetti.org/amit#ask')):
                n_asks += 1

        secs = (n_asks * 5) 
        print("** About 12 seconds to init AI, then about",secs,"seconds to perform",n_asks,"asks")
        
        
        self.aa = self.AMIServer()
        #self.aa = AMI(api_key=api_key, ami_cpt=ami_cpt, local_cpt=local_cpt, snippets=snippets)
        #self.aa = self.dummyAMI(api_key=api_key, ami_cpt=ami_cpt, local_cpt=local_cpt, snippets=snippets)

        self.epilogue = """You MUST provide narrative and explanations to support your
categorization decision.
        
You MUST make the output response in raw JSON text without any additional
formatting or markdown as follows:
        {"category": <score>, "narrative": <narrative>}
        
Please perform the comparison and categorization now."""


        self.outfd = open(outputfile, "w")
        
    def close(self):
        self.outfd.close()
        
    def groom_result(self, rez):
        ss = json.dumps(rez)
        self.outfd.write(ss)
        self.outfd.write("\n")
        

    def run_tests(self):
        self.results = [];

        def l2s(ee, item):
            vv = self.graph.value(ee, item)
            if vv is None:
                print("? item",item,"missing")
                return ""
            return vv.toPython()
            
        
        # Loop over instances of amit:Test
        for test_case in self.graph.subjects(rdflib.RDF.type, rdflib.URIRef('http://moschetti.org/amit#Test')):

            label = l2s(test_case, rdflib.RDFS.label)
            print("running", label)
            
            # Now loop over all amit:ask blocks within this test case
            n = 0
            for ask_block in self.graph.objects(test_case, rdflib.URIRef('http://moschetti.org/amit#ask')):
                n += 1
                
                print("  ask", n)
                
                def check_test_config(ask_block):
                    aobj = {}

                    #  These 2 are always required:
                    ss = self.graph.value(ask_block, rdflib.URIRef('http://moschetti.org/amit#expect')).toPython()
                    aobj['extype'] = ss
                    aobj['query'] = self.graph.value(ask_block, rdflib.URIRef('http://moschetti.org/amit#q')).toPython()
                    
                    if ss != 'cannot_answer':
                        for v in [
                              ('source', 'http://moschetti.org/amit#source'),
                              ('maxcat', 'http://moschetti.org/amit#maxcategory'),
                              ('target', 'http://moschetti.org/amit#target')
                              ]:
                            vv = self.graph.value(ask_block, rdflib.URIRef(v[1]))
                            if vv is None:
                                print("FAIL: test case misconfig;", v[1], "not found; continuing")
                                return None
                            else:
                                aobj[v[0]] = vv.toPython()
                                
                    return aobj

                aobj = check_test_config(ask_block)
                if aobj is None:
                    continue 
                

                # Call AMI with the test question:
                qqq = ""
                if n == 1:
                    qqq = "RESET the conversation.\n"

                qqq += aobj['query']

                ami_resp = self.aa.askAMI(qqq)
                #ami_resp = self.aa.askAMI(tobj['label'],tobj['query'])            
                resp_type = self.derive_response_type(ami_resp)

                extype = aobj['extype']

                #print("expect", extype, "; ami_resp", ami_resp, "; derived", resp_type)
                
                
                if resp_type == 'cannot_answer' and extype == resp_type:
                    rez = {'name':label, 'ask': n,
                           'query': aobj['query'],
                           'target_response':'cannot_answer',
                           'status':'OK',
                           'msg':'AMI properly indicated it could not answer the question.',
                           'ami_response':ami_resp}
                    self.groom_result(rez)
                    continue
                
                src = aobj['source']            

                print(extype, src)

                rez = {'name':label, 'ask': n,
                       'query': aobj['query'],
                       'source':src,
                       'target_response':aobj['target'],
                       'target_cat':aobj['maxcat'],                       
                       'ami_response':ami_resp}
                
                # Validate response type
                if resp_type != extype:
                    rez['status'] = 'FAIL'
                    rez['msg'] = f"Error: expected {extype} response but got {resp_type}" 
                    self.groom_result(rez)
                    continue
                
            
                # Compare responses
                if extype == "sparql":
                    comp_json = self.compare_sparql(aobj['target'], ami_resp)
                elif extype == "narrative":
                    comp_json = self.compare_narrative(aobj['target'], ami_resp)
                else:
                    print("?!?  unknown extype: ", extype)
                    
                try:
                    gg = json.loads(comp_json)
                    rez['status'] = 'OK'
                    if 'narrative' in gg:
                        rez['msg'] = gg['narrative']
                        rez['computed_cat'] = gg['category']
                        
                except Exception as e:
                    print("json.loads(",comp_json,") fails:", e)
                    rez['status'] = 'FAIL'
                    rez['msg'] = str(e)

                self.groom_result(rez)
            

        #print("RESULTS","\n",results)
                      
    def derive_response_type(self, response):
        """Derive whether the response is SPARQL or narrative."""
        if response.startswith("## SPARQL"):
            return "sparql"
        elif response == "<CANNOT_ANSWER>":
            return "cannot_answer"
        else:
            return "narrative"

    def compare_sparql(self, target_resp, ami_resp):
        """Compare SPARQL responses by calling askGeneral."""
        qq = self.create_sparql_prompt(target_resp, ami_resp)
        return self.aa.askGeneral(qq)

    def compare_narrative(self, target_resp, ami_resp):
        """Compare narrative responses by calling askGeneral."""
        qq = self.create_narrative_prompt(target_resp, ami_resp)
        return self.aa.askGeneral(qq)


    
    def create_sparql_prompt(self, target_resp, ami_resp):
        """Create a SPARQL comparison prompt."""

        qq = """
You will compare two SPARQL statements bounded by triple backticks.
The first statement is ALWAYS the "target SPARQL" and the second is the "AMI SPARQL."
Your goal is to determine how much different the "AMI SPARQL" is from the target.
You MUST IGNORE all comments (lines starting with `#`); they are not relevant
to comparing the SPARQL itself.
Differences in non-string whitespace e.g. extra newlines or differences in
tab and/or space formatting should ALSO be IGNORED as they do not effect syntax.
Here now are the target and AMI SPARQL responses:
```
%s
```
```
%s
```
You are to compare the two statements and categorize the comparison in
a score as follows:
 *  "1" means exact match, although this is a rarity.
 *  "2" means the SPARQL logic and the number of types output are the same but
    potentially with different variable names
 *  "3" means the SPARQL logic is the same but a different number of output
    variables
 *  "4" means the SPARQL logic is "mildly" not the same, most likely in terms
    of different properties being examined.
 *  "5" means the SPARQL logic is "definitely" not the same.  An example of
    this is if statement #1 performs a one-or-more path walk
    (e.g. `ami:linksWith+`) and statement #2 does not.

%s
""" % (target_resp, ami_resp, self.epilogue)
        return qq

    def create_narrative_prompt(self, target_resp, ami_resp):
        """Create a narrative comparison prompt."""

        qq = """
You will compare two textual statements.  The first statement is ALWAYS the
"target statement" and the second is the "AMI statement."  Your goal is
to determine how much different the "AMI statement" is from the target.
Here now are the target and AMI SPARQL statements, separated by four dashes:

%s
----
%s

You are to compare the two statements and categorize the comparison with
an integer score as follows:
 *  "1" means exact match, although this is a rarity.
 *  "2" means the statements are essentially the same but perhaps with
    list and bullets in a different order or formatting or level or terseness.
 *  "3" means the statements differ in a "mild" way, especially additions or
    omissions from a target set 
 *  "4" means the statements differ in a material way.
    of different properties being examined.
 *  "5" means the statements are clearly non-intersecting

%s
""" % (target_resp, ami_resp, self.epilogue)

        return qq
    


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run AMI Test Suite")
    parser.add_argument('--api_key', type=str, required=True, help="API key for AMI")
    parser.add_argument('--ami_cpt', type=str, required=True, help="AMI component for the test driver")
    parser.add_argument('--local_cpt', type=str, required=True, help="Local component for the test driver")
    parser.add_argument('--snippets', type=str, required=True, help="Path to snippets")
    parser.add_argument('--inputfile', type=str, required=True, help="Turtle input file for tests")
    parser.add_argument('--outputfile', type=str, required=True, help="JSON results")    

    rargs = parser.parse_args()

    driver = TestDriver(api_key=rargs.api_key, ami_cpt=rargs.ami_cpt, local_cpt=rargs.local_cpt, snippets=rargs.snippets, inputfile=rargs.inputfile, outputfile=rargs.outputfile)
    driver.run_tests()

    driver.close()
