import json

requests = {}

with open('requests.json', 'w', encoding='utf-8') as f:
  requests = json.load(f)
