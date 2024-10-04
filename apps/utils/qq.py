import json

import random
import string

# Set to store generated identifiers
identifier_set = set()

# List of words to avoid in the generated identifiers
blacklist_words = {"piss", "shit"}

# Function to generate a random alphanumeric string of length `n`
def generate_random_string(length=2):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# Function to generate a new identifier
def generate_identifier(domain_number):
    # Generate first 2 chars, number, and last 2 chars
    first_part = generate_random_string(2)
    last_part = generate_random_string(2)
    identifier = f"{domain_number}{first_part}{last_part}"
    
    return identifier

# Function to ensure the identifier is unique and avoids blacklisted words
def get_unique_identifier(domain_number):
    while True:
        identifier = generate_identifier(domain_number)
        
        # Check for blacklisted substrings
        if any(bad_word in identifier for bad_word in blacklist_words):
            continue  # Regenerate if the identifier contains a bad word
        
        # Ensure uniqueness
        if identifier not in identifier_set:
            identifier_set.add(identifier)
            return identifier

# Example usage
domain_number = '7sf'  # This would be the number (e.g., 7) + the domain (e.g., sf)
unique_id = get_unique_identifier(domain_number)
print(unique_id)

