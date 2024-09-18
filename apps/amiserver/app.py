from flask import Flask, request, session, jsonify
from flask_cors import CORS
from flask_session import Session

import uuid
import requests

import argparse


from AMI import AMI  # Assuming your AMI class is in a module

class AMIServer:
    def __init__(self, rargs, config=None):
        self.app = Flask(__name__)

        self.api_key = rargs.api_key
        self.ami_cpt = rargs.ami_cpt
        self.local_cpt = rargs.local_cpt
        self.snippets = rargs.snippets
        
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

            if question[0] == '!':
                response = ami_context.askGeneral(question)
            else:
                candidate = ami_context.askAMI(question)

                url = 'http://localhost:8080/query'
                headers = {
                    'Content-Type': 'application/sparql-query',  # or 'application/x-www-form-urlencoded'
                    'Accept': 'application/json'  # Expecting JSON results
                }
        
                if candidate == "<CANNOT ANSWER>":
                    print("** AMI cannot answer; asking global")
                    response = ami_context.askGeneral(question)
                else:
                    response = candidate
                    #  TBD: Need better way to separate SPARQL output from valid AMI output...
                    if "SELECT" in candidate:
                        print("** calling jenaserver...")

                        response = requests.post(url, data=candidate, headers=headers)
                        response = response.text                
                        emitResponse(response)                

            return jsonify({'response': response})

        @self.app.route('/stash', methods=['POST'])
        def handle_stash():
            user_id = session.get('user_id')
            if user_id is None or user_id not in self.ami_contexts:
                return jsonify({'error': 'Session not found'}), 400

            # Simulate stashing data for this user
            data = request.json
            stash = data.get('stash')

            if stash == 'yes':
                return jsonify({'message': 'Data stashed successfully'})
            else:
                return jsonify({'message': 'Data not stashed'})

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
