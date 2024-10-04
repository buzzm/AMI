import rdflib
import json

import requests


from AMI import AMI  # Assuming your AMI class is in a module

class TestDriver:

    class dummyAMI:
        def __init__(self, api_key, ami_cpt, local_cpt, snippets):
            pass

        def askAMI(self, lbl, test_query):
            print("dummy askAMI():","\n",test_query)
            return "foo"

        def askGeneral(self, test_query):
            return("""{"category":0, "narrative":"dummy"}""")

    class AMIServer:
        def __init__(self, api_key, ami_cpt, local_cpt, snippets):
            pass

        def askAMI(self, test_query):
            url = 'http://localhost:5001/sparql'

            hdrs = { 'Content-Type': 'application/json' }

            data = json.dumps({"question": test_query,"systemSize": "Simple"})
            
            response = requests.post(url, data=data, headers=hdrs)

            narrative = "<CANNOT_ANSWER>"
            if response.status_code == 200:
                qq = response.json()
                narrative = qq['narrative']
            return narrative

        def askGeneral(self, test_query):
            return self.askAMI("!" + test_query)  # oooo!
    

    def __init__(self, api_key, ami_cpt, local_cpt, snippets, inputfile):
        self.aa = self.AMIServer(api_key=api_key, ami_cpt=ami_cpt, local_cpt=local_cpt, snippets=snippets)
        #self.aa = AMI(api_key=api_key, ami_cpt=ami_cpt, local_cpt=local_cpt, snippets=snippets)
        #self.aa = self.dummyAMI(api_key=api_key, ami_cpt=ami_cpt, local_cpt=local_cpt, snippets=snippets)

        self.epilogue = """You MUST provide narrative and explanations to support your
categorization decision.
        
You MUST make the output response in raw JSON text without any additional
formatting or markdown as follows:
        {"category": <score>, "narrative": <narrative>}
        
Please perform the comparison and categorization now."""

        
        self.graph = rdflib.Graph()
        self.graph.parse(inputfile, format="ttl")

    def run_tests(self):

        results = [];
        
        # Loop over instances of amit:Test
        for test_case in self.graph.subjects(rdflib.RDF.type, rdflib.URIRef('http://moschetti.org/amit#Test')):

            def l2s(test_case, item):
                return self.graph.value(test_case, item).toPython()
            
            tobj = {
                'label': l2s(test_case, rdflib.RDFS.label),
                'query': l2s(test_case, rdflib.URIRef('http://moschetti.org/amit#q')),
                'extype': l2s(test_case, rdflib.URIRef('http://moschetti.org/amit#expect')),
                'response': l2s(test_case, rdflib.URIRef('http://moschetti.org/amit#response'))
            }

            label = tobj['label']
            print("running", label)
                        
            # Call AMI with the test question
            ami_resp = self.aa.askAMI(tobj['query'])
            #ami_resp = self.aa.askAMI(tobj['label'],tobj['query'])            
            resp_type = self.derive_response_type(ami_resp)

            extype = tobj['extype']


            rez = {'name':label }
                
            # Validate response type

            for et in ['sparql','narrative','cannot_answer']:
                 if extype == et and resp_type != et:
                     rez['status'] = 'FAIL'
                     rez['msg'] = f"Error: expected {et} response but got {resp_type}" 
                     results.append(rez)
                     continue
                
            # if extype == "sparql" and resp_type != "sparql":
            #     print(f"Error: expected SPARQL response but got {resp_type}")
            #     continue
            # elif extype == "narrative" and resp_type != "narrative":
            #     print(f"Error: expected narrative response but got {resp_type}")
            #     continue
            # elif extype == "cannot_answer" and resp_type != "cannot_answer":
            #     print(f"Error: expected cannot_answer response but got {resp_type}")
            #     continue            

            # Compare responses
            if extype == "sparql":
                comp_json = self.compare_sparql(tobj['response'], ami_resp)
            elif extype == "narrative":
                comp_json = self.compare_narrative(tobj['response'], ami_resp)

            try:
                gg = json.loads(comp_json)
                rez['status'] = 'OK'
                if 'narrative' in gg:
                    rez['msg'] = gg['narrative']
                    rez['category'] = gg['category']                    
                
            except Exception as e:
                print("json.loads(",comp_json,") fails:", e)
                rez['status'] = 'FAIL'
                rez['msg'] = str(e)

            results.append(rez)

        print("RESULTS","\n",results)
                      
    def derive_response_type(self, response):
        """Derive whether the response is SPARQL or narrative."""
        if response.startswith("## SPARQL"):
            return "sparql"
        elif response == "<CANNOT ANSWER>":
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

    rargs = parser.parse_args()

    driver = TestDriver(api_key=rargs.api_key, ami_cpt=rargs.ami_cpt, local_cpt=rargs.local_cpt, snippets=rargs.snippets, inputfile=rargs.inputfile)
    driver.run_tests()
