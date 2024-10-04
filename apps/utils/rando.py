#
#
#  Testbed to see how fast we run out of numbers
#
#
import random
import string


# Set to store generated identifiers
identifier_set = set()

def generate_random_string(length=2):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_random_num():
    return ''.join(random.choices(string.digits, k=1))


# Function to generate a new identifier
def generate_identifier():

    atoms = 2

    identifier = ""
    
    for n in range(0, atoms):
        num = generate_random_num()
        ascii_part = generate_random_string(2)
        
        identifier += f"{num}{ascii_part}"
    
    return identifier

global x;

# Function to ensure the identifier is unique and avoids blacklisted words
def get_unique_identifier():
    n = 0
    while True:
        identifier = generate_identifier()
        
        # Ensure uniqueness
        if identifier not in identifier_set:
            identifier_set.add(identifier)
            if n > 3:
                print("took",n,"tries to fix collision at set size", len(identifier_set))
            return identifier

        n += 1
            
# Example usage
print("example: " , get_unique_identifier())

for n in range(0,100000000):
    unique_id = get_unique_identifier()
    if n < 3:
        print(unique_id)
        
    if unique_id == "2qt4uu":
        print("Got",unique_id, "in",n,"tries")
        break
    
#    if 0 == n % 10_000_000:
#        print(n, "...")

print("done with", n, "tries")
