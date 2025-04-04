import os
import json
import sys
from urllib.parse import urlparse

def extract_query_url(api_endpoint):
    parsed_url = urlparse(api_endpoint)
    path_parts = parsed_url.path.split('/v1/')
    if len(path_parts) > 1:
        query_url = '/v1/' + path_parts[1].split('?')[0]
        return query_url
    return None

def load_krakend_json(filename='krakend.json'):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def find_endpoint(data, query_url):
    endpoints = data.get("endpoints", [])
    for endpoint in endpoints:
        if endpoint.get("endpoint") == query_url:
            return endpoint
    return None

def main(api_endpoint):
    query_url = extract_query_url(api_endpoint)
    if not query_url:
        print("Error processing API endpoint")
        return

    if not os.path.exists('krakend.json'):
        print("krakend.json file not found")
        return

    krakend_data = load_krakend_json()
    endpoint_data = find_endpoint(krakend_data, query_url)

    if endpoint_data:
        print(json.dumps(endpoint_data, indent=2))
    else:
        print("No endpoint found for this query_url")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <API_ENDPOINT>")
        sys.exit(1)

    api_endpoint = sys.argv[1]
    main(api_endpoint)