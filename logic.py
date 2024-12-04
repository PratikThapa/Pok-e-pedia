import requests
import json
import time
import os

# The API to fetch the required data about Pokemon
POKEAPI_URL = "https://pokeapi.co/api/v2/pokemon/"
POKEAPI_SPECIES_URL = "https://pokeapi.co/api/v2/pokemon-species/"
POKEAPI_EVOLUTION_URL = "https://pokeapi.co/api/v2/evolution-chain/"

CACHE_FILE = "pokemon_cache.json"
CACHE_EXPIRY_TIME = 3600  # Cache expiration time (1 hour in seconds)

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as cache_file:
        CACHE = json.load(cache_file)
else:
    CACHE = {}
    
def is_cache_expired(timestamp):
    current_time = time.time()
    return (current_time - timestamp) > CACHE_EXPIRY_TIME

def save_cache():
    with open(CACHE_FILE, 'w') as cache_file:
        json.dump(CACHE, cache_file)

def fetch_pokemon_data(pokemon_name):
    pokemon_name = pokemon_name.lower()
    if pokemon_name in CACHE:
        return CACHE[pokemon_name]

    response = requests.get(POKEAPI_URL + pokemon_name)
    if response.status_code == 200:
        data = response.json()
        parsed_data = {
            'name': data['name'],
            'weight': data['weight'] / 10,
            'height': data['height'] / 10,
            'sprites': data['sprites'],
            'species_url': data['species']['url'],
            'moves': [move['move']['name'] for move in data['moves']],
            'types': [t['type']['name'] for t in data['types']]
        }
        CACHE[pokemon_name] = parsed_data
        save_cache()
        return parsed_data
    return None

def fetch_species_data(species_url):
    if species_url in CACHE:
        return CACHE[species_url]

    response = requests.get(species_url)
    if response.status_code == 200:
        species_data = response.json()
        CACHE[species_url] = species_data
        save_cache()
        return species_data
    return None

def fetch_evolution_data(species_url):
    species_data = fetch_species_data(species_url)
    if species_data:
        evolution_chain_url = species_data['evolution_chain']['url']
        if evolution_chain_url in CACHE and not is_cache_expired(CACHE[evolution_chain_url].get('timestamp', 0)):
            return CACHE[evolution_chain_url]

        try:
            response = requests.get(evolution_chain_url)
            response.raise_for_status()
        except requests.RequestException:
            return None

        if response.status_code == 200:
            evolution_data = response.json()
            CACHE[evolution_chain_url] = evolution_data
            save_cache()
            return evolution_data
    return None