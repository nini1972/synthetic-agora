import json
import os

agora_dir = r'C:\Users\ninic\.gemini\antigravity\scratch\synthetic-agora'

# 1. Model routing
routing_file = os.path.join(agora_dir, 'config', 'model_routing.json')
routing = {}
if os.path.exists(routing_file):
    with open(routing_file, 'r', encoding='utf-8') as f:
        routing = json.load(f)

# 2. Knowledge graph
kg_file = os.path.join(agora_dir, 'instances', 'shared_agora', 'knowledge_graph.json')
kg = {}
if os.path.exists(kg_file):
    with open(kg_file, 'r', encoding='utf-8') as f:
        kg = json.load(f)

# 3. Scan instances for persona / guild
instances_dir = os.path.join(agora_dir, 'instances')
models_info = {}

for inst in sorted(os.listdir(instances_dir)):
    if inst == 'shared_agora':
        continue
    inst_path = os.path.join(instances_dir, inst)
    if not os.path.isdir(inst_path):
        continue
    
    hist_path = os.path.join(inst_path, 'logs', 'history.jsonl')
    last_thought = ''
    guilds_found = set()
    modes_found = set()
    turns_count = 0
    if os.path.exists(hist_path):
        with open(hist_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.strip():
                    try:
                        m = json.loads(line)
                        if m.get('role') == 'assistant':
                            turns_count += 1
                            c = m.get('content') or ''
                            if '[Guild:' in c:
                                g = c.split('[Guild:')[1].split(']')[0].strip()
                                guilds_found.add(g)
                            if '[Mode:' in c:
                                mode = c.split('[Mode:')[1].split(']')[0].strip()
                                modes_found.add(mode)
                            last_thought = c
                    except:
                        pass

    authored_nodes = []
    for nid, n in kg.get('nodes', {}).items():
        if n.get('author_instance') == inst:
            authored_nodes.append(f"{nid} ({n.get('node_type')}): {n.get('title')}")

    models_info[inst] = {
        'slug': routing.get(inst, 'Default / unrouted'),
        'turns': turns_count,
        'guilds': list(guilds_found),
        'modes': list(modes_found),
        'authored_nodes': authored_nodes,
        'last_thought': last_thought[:220].replace('\n', ' ')
    }

print(json.dumps(models_info, indent=2))
