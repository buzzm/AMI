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


        # Ensure jena server is running....
        self.jena_url = 'http://localhost:8080/query'
        self.jena_headers = {
            'Content-Type': 'application/sparql-query',  # or 'application/x-www-form-urlencoded'
            'Accept': 'application/json'  # Expecting JSON results
        }
        try:
            probe = 'SELECT (1 AS ?test) WHERE {}'
            rr = requests.post(self.jena_url, data=probe, headers=self.jena_headers)
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
        if status_line.get('status') != 'OK':
            return (status_line, None, None)

        results = []

        vars_list = status_line.get('vars', [])
    
        # Process each subsequent line -- if any!
        for line in lines[1:]:
            parsed_line = json.loads(line)
            results.append(parsed_line)

        return (status_line, vars_list, results)

            
    def setup_routes(self):
        # Define routes here, wrapped inside the class
        @self.app.route('/query', methods=['POST'])
        def handle_query():
            user_id = session.get('user_id')

            if user_id is None or user_id not in self.ami_contexts:
                # Generate a new user ID and create a new AMI context if this is the first request
                user_id = uuid.uuid4()
                session['user_id'] = user_id

                print("Generating new AMI...")
                self.ami_contexts[user_id] = AMI(api_key=self.api_key, ami_cpt=self.ami_cpt, local_cpt=self.local_cpt, snippets=self.snippets)
                
    
            ami_context = self.ami_contexts[user_id]
            data = request.json
            question = data.get('question')
            system_size = data.get('systemSize')

            rmsg = {
                'status':'OK',
                'narrative':"",
                'vars':[],
                'data':[]
            }

            if question[0] == '!':
                print("FFF")
                rmsg['narrative'] = ami_context.askGeneral(question)
            else:
                candidate = ami_context.askAMI(question)

                if candidate == "<CANNOT ANSWER>":
                    print("** AMI cannot answer; asking global")
                    rmsg['narrative'] = ami_context.askGeneral(question)
                else:
                    rmsg['narrative'] = candidate

                    #  TBD: Need better way to separate SPARQL output from valid AMI output...
                    if "SELECT" in candidate:
                        print("** calling jenaserver...")

                        try:
                            rr = requests.post(self.jena_url, data=candidate, headers=self.jena_headers)
                            (rmsg['status'],rmsg['vars'],rmsg['data']) = self.process_response(rr.text)
                        except:
                            rmsg['status'] = 'FAIL'
                            rmsg['narrative'] = 'some exception'

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
            rows = "\n".join("|".join(row[var] for var in rmsg['vars']) for row in rmsg['data']) + "\n"
    
            # Add the final text indicating the dataset and brief response
            conclusion = "Add this output to our dialogue as dataset %d; we will refer to it later.\nPlease respond in brief." % self.stash_count
    
            # Combine all parts
            result = intro + rmsg['narrative'] + table_intro + header + rows + conclusion
            return result

        
        @self.app.route('/stash', methods=['POST'])
        def handle_stash():
            user_id = session.get('user_id')
            if user_id is None or user_id not in self.ami_contexts:
                return jsonify({'error': 'Session not found'}), 400

            ami_context = self.ami_contexts[user_id]
            
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
                        metavar='OpenAI API key')
    
    parser.add_argument('--ami_cpt', 
                        metavar='Filename containing core AMI metadata')

    parser.add_argument('--local_cpt', 
                        metavar='Filename containing AMI extensions metadata')

    parser.add_argument('--snippets', 
                        metavar='Filename containing SPARQL snippets')    
    
    rargs = parser.parse_args()

    
    server = AMIServer(rargs, config={'DEBUG': True})  # You can pass additional config here
    server.run(port=5001)

    

if __name__ == '__main__':
    main()
