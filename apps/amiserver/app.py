import os
import uuid
import argparse
import threading
import time
import json

import requests

from flask import Flask, request, session, jsonify
from flask_cors import CORS
from flask_session import Session




from AMI import AMI  # Assuming your AMI class is in a module

class AMIServer:
    expensive_initialized = False  # Class-level flag to track initialization
    
    def __init__(self, rargs, config=None):
        self.app = Flask(__name__)

        self.api_key = rargs.api_key
        self.ami_cpt = rargs.ami_cpt
        self.local_cpt = rargs.local_cpt
        self.snippets = rargs.snippets
        self.onectx = rargs.onectx
        self.numctx = rargs.numctx

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

        #  Because initializing the LLM with prompts and such takes such a long
        #  time, upon startup we pre-allocate a bunch of them -- and
        #  only ONCE:
        
        self.ami_contexts = [None] * self.numctx
        self.slot_assign = [None] * self.numctx  # Initially, array of None       
        self.ami_context_usage = [None] * self.numctx  # An array of timestamps....

        # Get this out of the way upon startup...
        if self.onectx:        
            print("Generating onectx AMI...")
            self.ami_contexts['XXX'] = AMI(api_key=self.api_key, ami_cpt=self.ami_cpt, local_cpt=self.local_cpt, snippets=self.snippets)
        else:
            self.initialize_contexts()
            # Start the background timer for releasing inactive slots
            self.start_slot_timer()

            

    def initialize_contexts(self):
        print(f"Preallocating {self.numctx} AMI contexts...")
        for i in range(self.numctx):
            self.ami_contexts[i] = AMI(api_key=self.api_key, ami_cpt=self.ami_cpt, local_cpt=self.local_cpt, snippets=self.snippets)
            self.ami_context_usage[i] = time.time()  # Track the initial allocation time

    def start_slot_timer(self):
        def monitor_slots():
            while True:
                current_time = time.time()
                for idx, last_used in enumerate(self.ami_context_usage):
                    delta = current_time - last_used;
                    #print("check",idx,last_used, delta)

                    # 2 minutes of inactivity -- but if the slot is ALREADY None,
                    # leave it alone!
                    if current_time - last_used > 120 and self.slot_assign[idx] is not None:
                        print(f"Releasing inactive slot {idx}...")
                        self.slot_assign[idx] = None

                        # This is key!  Rebuild a completely NEW API context.
                        # This will take time.
                        self.ami_contexts[idx] = AMI(api_key=self.api_key, ami_cpt=self.ami_cpt, local_cpt=self.local_cpt, snippets=self.snippets)
                        self.ami_context_usage[idx] = time.time()
                        
                time.sleep(10)  # Check every 10 seconds

        timer_thread = threading.Thread(target=monitor_slots)
        timer_thread.daemon = True  # Allow thread to exit when the main program exits
        timer_thread.start()

            
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


    
    def assign_ami_ctx(self):
        """Find a slot and return AMI context there or None if
        no available slots"""
        
        # Try to assign a new context if any slot is available
        available_slot = -1
        ami_context = None
        
        for index, uu in enumerate(self.slot_assign):
            if uu is None:
                available_slot = index
                break
            
        print("user_id is NONE; slot search yields", available_slot)
            
        if available_slot != -1:
            user_id = uuid.uuid4()
                        
            # Assign the user to the available slot
            self.slot_assign[available_slot] = user_id
            self.ami_context_usage[available_slot] = time.time()
                        
            session['user_id'] = user_id

            print("assign", user_id, "to slot", available_slot)
                
            ami_context = self.ami_contexts[available_slot]

        return ami_context
    
    
    def setup_routes(self):
        # Define routes here, wrapped inside the class

        @self.app.route('/intro', methods=['GET'])
        def handle_intro():
            n_open = 0
            for uu in self.slot_assign:
                if uu == None:
                    n_open += 1
                    
            html = """
<HTML>
Hello! I am AMI.  You can ask me questions about a technology footprint such as "What software in AMI is going EOL this year?" or "What systems depend on postgres 16.3?"
            
<p>
Due the resource-intense nature of LLM processing and with an eye toward frugality, there is a current max of %d simultaneous users.  If such a "slot is available, you will be assigned to the slot.  Note that your session context (and your conversational history) will be lost after 2 minutes of inactivity.  There are currently %d open slots.               

<br>            
If no slots are available, try pressing 'GO' again in a few minutes.
<p>
</HTML>
""" % (self.numctx, n_open)           
            return html
        
            
        @self.app.route('/sparql', methods=['POST'])
        def handle_query():

            user_id = session.get('user_id')

            if self.onectx:
                ami_context = self.ami_contexts['XXX']
            else:
                index = -1
                if user_id is not None:
                    index = self.slot_assign.index(user_id) if user_id in self.slot_assign else -1

                    if index != -1:
                        print("matched user_id", user_id)
                    
                        # Update the context's last used time
                        self.ami_context_usage[index] = time.time()

                        # ALWAYS produces valid AMI context:
                        ami_context = self.ami_contexts[index] 

                    else:
                        print("user_id OK", user_id, "but unmatched; likely timed out; create new one")
                        ami_context = self.assign_ami_ctx() 
                        
                else:
                    print("user_id is NONE; initiate slot search...")
                    ami_context = self.assign_ami_ctx()

                    
            if ami_context == None:
                # No available slots
                print("no slots; try later")                        
                return jsonify({
                    'status': 'FAIL',
                    'narrative': f"All {self.numctx} slots are currently being used; try again later.",
                    'source': 'AMI',
                    'vars': [],
                    'data': []
                })
                    

            data = request.json
            question = data.get('question')
            system_size = data.get('systemSize')

            print("ami_context:", ami_context)
            
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

    parser.add_argument('--numctx',
                        required=True,
                        type=int,
                        help='Number of slots to preallocate.')
    
    rargs = parser.parse_args()

    
    server = AMIServer(rargs, config={'DEBUG': True})  # You can pass additional config here

    print("** server created")
    
    server.run(host='0.0.0.0', port=5001)

    

if __name__ == '__main__':
    main()
