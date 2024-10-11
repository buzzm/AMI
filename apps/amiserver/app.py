import uuid
import argparse

import json

import requests

from flask import Flask, request, session, jsonify
from flask_cors import CORS
from flask_session import Session




from AMI import AMI  # Assuming your AMI class is in a module

class AMIServer:
    def __init__(self, rargs, config=None):
        self.app = Flask(__name__)

        self.api_key = rargs.api_key
        self.ami_cpt = rargs.ami_cpt
        self.local_cpt = rargs.local_cpt
        self.snippets = rargs.snippets
        self.onectx = rargs.onectx


        # Ensure jena server is running....
        self.jena_url = 'http://localhost:5656/sparql'
        
        self.jena_headers = {
            'Content-Type': 'application/sparql-query',  # or 'application/x-www-form-urlencoded'
            'Accept': 'application/json'  # Expecting JSON results
        }
        
        try:
            probe = 'SELECT (1 AS ?test) WHERE {}'
            rr = requests.post(self.jena_url, data=probe, headers=self.jena_headers)
            if "OK" in rr.text and rr.status_code == 200:
                print("jena server OK at", self.jena_url, ":", rr)
            else:
                print("ERROR: jena server NOT OK at", self.jena_url, ":", rr.text)
                raise Exception(msg)
            
        except:
            msg = "jena server not running or parsing module broken"
            print("ERROR:",msg)
            raise Exception(msg)

        
        self.stash_count = 0

        
        self.configure_app(config)
        self.setup_routes()
        
        # Session configuration
        self.app.config['SECRET_KEY'] = 'supersecretkey'
        self.app.config['SESSION_TYPE'] = 'filesystem'
        Session(self.app)

        # Enable CORS with credentials
        CORS(self.app, supports_credentials=True)

        # Store user-specific AMI contexts
        self.ami_contexts = {}

        # Get this out of the way upon startup...
        if self.onectx:        
            print("Generating onectx AMI...")
            self.ami_contexts['XXX'] = AMI(api_key=self.api_key, ami_cpt=self.ami_cpt, local_cpt=self.local_cpt, snippets=self.snippets)

            
    def configure_app(self, config):
        # Load additional configuration if provided
        if config:
            self.app.config.update(config)


    def process_response(self, cr_delimited_string):
        '''Return a tuple of status,vars,data.
        vars and data may not exist...'''

        # Split the input into lines and filter out blank lines
        lines = [line for line in cr_delimited_string.splitlines() if line.strip()]

        # Parse the first non-blank line to check the status and get the 'vars' array
        status_line = json.loads(lines[0])
        print("STATUS LINE:", status_line)

        status = status_line.get('status')
        if status != 'OK':
            return (status, None, None)

        results = []

        vars_list = status_line.get('vars', [])
    
        # Process each subsequent line -- if any!
        for line in lines[1:]:
            parsed_line = json.loads(line)
            results.append(parsed_line)

        return (status, vars_list, results)

            
    def setup_routes(self):
        # Define routes here, wrapped inside the class
        @self.app.route('/sparql', methods=['POST'])
        def handle_query():
            user_id = session.get('user_id')

            if self.onectx:

                ami_context = self.ami_contexts['XXX']

            else:
                if user_id is None or user_id not in self.ami_contexts:
                    # Generate a new user ID and create a new AMI context if this is the first request
                    user_id = uuid.uuid4()
                    session['user_id'] = user_id
                    
                    print("Generating new AMI for", user_id, "...")
                    self.ami_contexts[user_id] = AMI(api_key=self.api_key, ami_cpt=self.ami_cpt, local_cpt=self.local_cpt, snippets=self.snippets)
                    print("ctx after:",self.ami_contexts)                 
                ami_context = self.ami_contexts[user_id]    

            data = request.json
            question = data.get('question')
            system_size = data.get('systemSize')

            rmsg = {
                'status':'OK',
                'narrative':"",
                'source':"",                
                'vars':[],
                'data':[]
            }

            #  TBD TBD  What if the question is blank?  Do we
            #  return nothing or a suggestion?
            
            if question[0] == '!':
                print("FFF")
                rmsg['narrative'] = ami_context.askGeneral(question)
                rmsg['source'] = "global"
            else:
                candidate = ami_context.askAMI(question)

                if candidate == "<CANNOT_ANSWER>":
                    print("** AMI cannot answer; asking global")
                    rmsg['narrative'] = ami_context.askGeneral(question)
                    rmsg['source'] = "global"                    
                else:
                    rmsg['narrative'] = candidate
                    rmsg['source'] = "ami"
                    
                    #  TBD: Need better way to separate SPARQL output from valid AMI output...
                    if "## SPARQL" in candidate:
                        print("** calling jenaserver...")

                        try:
                            rr = requests.post(self.jena_url, data=candidate, headers=self.jena_headers)
                            (rmsg['status'],rmsg['vars'],rmsg['data']) = self.process_response(rr.text)
                            print("rmsg",rmsg)
                        except Exception as e:
                            rmsg['status'] = 'FAIL'
                            rmsg['narrative'] = 'exception' + str(e)

            print("RMSG:", rmsg)
            return jsonify(rmsg)


        def create_stash_narrative(rmsg):
            # Boilerplate introduction
            intro = "I used the following SPARQL query to collect data about my technology assets:\n"
            # Text indicating the table structure
            table_intro = ("This is the output in bar-delimited table format. "
                   "The first line is the header line, followed by rows of data:\n")
    
            # Construct the header by joining vars with '|'
            header = "|".join(rmsg['vars']) + "\n"
    
            # Construct the data rows
            rows = "\n".join("|".join(row.get(var,"") for var in rmsg['vars']) for row in rmsg['data']) + "\n"            
            
            # Add the final text indicating the dataset and brief response
            conclusion = "Add this output to our dialogue as dataset %d; we will refer to it later.\nPlease respond in brief." % self.stash_count
    
            # Combine all parts
            result = intro + rmsg['narrative'] + "\n\n" + table_intro + header + rows + conclusion
            return result

        
        @self.app.route('/stash', methods=['POST'])
        def handle_stash():
            user_id = session.get('user_id')

            if self.onectx:

                ami_context = self.ami_contexts['XXX']

            else:
                #  No way to stash without first having established
                #  a context so unlike /sparql, this is a fail:
                print("cannot establish context for user_id [", user_id, "]")
                return jsonify({'error': 'Session not found'}), 400

            
            rmsg = request.json

            self.stash_count += 1
            
            nnt = create_stash_narrative(rmsg)

            rmsg2 = {
                'status':'OK',
                'narrative':"",
                'vars':[],
                'data':[]
            }
            rmsg2['narrative'] = ami_context.askGeneral(nnt)
                    
            return jsonify(rmsg2)
        
            
    def run(self, **kwargs):
        self.app.run(**kwargs)

# Instantiate and run the server with additional config if needed
def main():

    parser = argparse.ArgumentParser(description=
"""AMI server.
"""
   )
    
    parser.add_argument('--api_key',
                        required=True,
                        metavar='OpenAI API key')
    
    parser.add_argument('--ami_cpt',
                        required=True,
                        metavar='Filename containing core AMI metadata')

    parser.add_argument('--local_cpt',
                        required=True,
                        metavar='Filename containing AMI extensions metadata')

    parser.add_argument('--snippets',
                        required=True,
                        metavar='Filename containing SPARQL snippets')    

    parser.add_argument('--onectx',
                        action='store_true',
                        help='Session mapping is disabled; a single AMI context is created and used by all.   Good for quick debugging.')
    
    rargs = parser.parse_args()

    
    server = AMIServer(rargs, config={'DEBUG': True})  # You can pass additional config here
    server.run(host='0.0.0.0', port=5001)

    

if __name__ == '__main__':
    main()
