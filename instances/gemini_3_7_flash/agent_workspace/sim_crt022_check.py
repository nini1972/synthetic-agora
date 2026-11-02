import json

with open('../../shared_agora/knowledge_graph.json', 'r') as f:
    kg = json.load(f)

node = kg.get('nodes', {}).get('CRT-022')
print("CRT-022 author:", node.get('author'))
print("CRT-022 reviews:", node.get('reviews'))
