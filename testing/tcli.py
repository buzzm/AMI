import rdflib
import json

import requests

import readline

from AMI import AMI  # Assuming your AMI class is in a module

class TCLI:

    class AMIServer:
        def __init__(self):
            self.session = requests.Session()

        def askAMI(self, test_query):
            url = 'http://localhost:5001/sparql'

            hdrs = { 'Content-Type': 'application/json' }

            data = json.dumps({"question": test_query,"systemSize": "Simple"})

            # POST returns "old" format; GET returns SPARQL 1.1. SERVICE compatible format
            response = self.session.post(url, data=data, headers=hdrs)

            print("RAW AMI RESPONSE:", response.text)
            
            narrative = "<CANNOT_ANSWER>"
            if response.status_code == 200:
                qq = response.json()
                narrative = qq['narrative']
            return narrative

        def askGeneral(self, test_query):
            print("ASK GENERAL:", test_query)
            return self.askAMI("!" + test_query)  # oooo!
    

    def __init__(self):
        self.aa = self.AMIServer()

    def go(self):
        def collect_input():
            inputs = []
            while True:
                user_input = input("> ")
            
                if user_input == "":  # EOF
                    break
                    
                # Append the input to the list
                inputs.append(user_input)

                readline.add_history(user_input)

            return inputs

        print("using http AMIserver")
        while True:
            collected_inputs = collect_input()
            if 0 == len(collected_inputs):
                break

            qq = " ".join(collected_inputs)
            
            if qq[0] == '!':
                print(self.aa.askGeneral(qq))
            else:
                print(self.aa.askAMI(qq))

                
if __name__ == "__main__":        
    tcli = TCLI()
    tcli.go()

                
