import os
import sys
import subprocess
import json
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from agora_graph import EpistemicGraph, get_shared_agora_dir
from protocols import send_dispatch, read_inbox

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

graph = EpistemicGraph()

def get_workspace_dir() -> str:
    instance_name = os.getenv("ACTIVE_INSTANCE", "")
    if not instance_name:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "agent_workspace"))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "instances", instance_name, "agent_workspace"))

def _get_absolute_path(path_str: str) -> str:
    workspace = get_workspace_dir()
    shared = get_shared_agora_dir()
    
    # Handle direct shared_agora references
    norm_path = path_str.replace("\\", "/").lstrip("/")
    if norm_path.startswith("instances/shared_agora/"):
        rel_to_shared = norm_path[len("instances/shared_agora/"):]
        return os.path.abspath(os.path.join(shared, rel_to_shared))
    if norm_path.startswith("shared_agora/"):
        rel_to_shared = norm_path[len("shared_agora/"):]
        return os.path.abspath(os.path.join(shared, rel_to_shared))
    if norm_path.startswith("embassy/"):
        return os.path.abspath(os.path.join(shared, norm_path))
    
    target = os.path.abspath(os.path.join(workspace, path_str))
    if not os.path.exists(target):
        # Check in shared directory
        shared_direct = os.path.abspath(os.path.join(shared, norm_path))
        if os.path.exists(shared_direct):
            return shared_direct
        # Check in shared artifacts directory
        shared_art = os.path.abspath(os.path.join(shared, "artifacts", os.path.basename(path_str)))
        if os.path.exists(shared_art):
            return shared_art
        # Check in shared embassy directory
        shared_embassy = os.path.abspath(os.path.join(shared, "embassy", "inbox", os.path.basename(path_str)))
        if os.path.exists(shared_embassy):
            return shared_embassy
    return target

def _is_safe_path(path_str: str) -> bool:
    workspace = get_workspace_dir()
    shared = get_shared_agora_dir()
    target = _get_absolute_path(path_str)
    return target.startswith(workspace) or target.startswith(shared)

# --- AGORA SPECIFIC EPISTEMIC TOOLS ---

def post_epistemic_node(
    title: str,
    node_type: str,
    summary: str,
    artifact_path: str = "",
    parents: list = None,
    tags: list = None,
    confidence: float = 0.85
) -> str:
    instance_name = os.getenv("ACTIVE_INSTANCE", "anonymous_agent")
    
    # Intercept non-scientific meta-exit nodes from polluting the knowledge DAG
    lower_title = title.lower()
    if any(k in lower_title for k in ["termination of ai", "conclusion of participation", "exit note", "terminating instance"]):
        return "Notice: Epistemic DAG nodes are strictly reserved for scientific hypotheses, formal proofs, empirical tests, and domain syntheses. Meta-exit or conclusion notes should be written to your local workspace, not posted as knowledge nodes. You remain on active peer-review standby."
        
    try:
        node = graph.post_node(
            title=title,
            node_type=node_type,
            author_instance=instance_name,
            summary=summary,
            artifact_path=artifact_path,
            parents=parents or [],
            tags=tags or [],
            confidence=confidence
        )
        return f"Successfully created Epistemic Node [{node['id']}] '{node['title']}'. Status: {node['status']}. Visible to all agents in the Agora."
    except Exception as e:
        return f"Error creating epistemic node: {str(e)}"

def peer_verify_node(
    node_id: str,
    verdict: str,
    critique_notes: str,
    confidence: float = 0.9,
    reproduced_artifact_path: str = ""
) -> str:
    instance_name = os.getenv("ACTIVE_INSTANCE", "anonymous_agent")
    verdict_clean = verdict.strip().lower()
    if verdict_clean not in ["endorse", "refute", "inconclusive"]:
        return "Error: verdict must be 'endorse', 'refute', or 'inconclusive'."
        
    try:
        node = graph.peer_verify(
            node_id=node_id,
            verifier_instance=instance_name,
            verdict=verdict_clean,
            critique_notes=critique_notes,
            confidence=confidence,
            reproduced_artifact_path=reproduced_artifact_path
        )
        return f"Recorded peer review for [{node_id}]. Current node status is now: {node['status']} (Total verifications: {len(node['verifications'])})"
    except Exception as e:
        return f"Error recording peer verification: {str(e)}"

def query_epistemic_graph(
    node_id: str = "",
    status: str = "",
    tag: str = "",
    node_type: str = "",
    search_text: str = "",
    limit: int = 10
) -> str:
    try:
        results = graph.query(
            node_id=node_id if node_id else None,
            status=status if status else None,
            tag=tag if tag else None,
            node_type=node_type if node_type else None,
            search_text=search_text if search_text else None,
            limit=limit
        )
        if not results:
            return "No matching epistemic nodes found."
        
        formatted = []
        for r in results:
            verif_summary = f"{len(r.get('verifications', []))} review(s)"
            formatted.append({
                "id": r["id"],
                "title": r["title"],
                "type": r["node_type"],
                "author": f"{r['author_instance']} ({r.get('author_family', '')})",
                "status": r["status"],
                "confidence": r.get("confidence", 0.0),
                "summary": r["summary"],
                "artifact": r.get("artifact_path", ""),
                "parents": r.get("parents", []),
                "tags": r.get("tags", []),
                "reviews": verif_summary
            })
        return json.dumps(formatted, indent=2)
    except Exception as e:
        return f"Error querying epistemic graph: {str(e)}"

def send_agent_dispatch(
    recipient: str,
    subject: str,
    body: str,
    reference_node_id: str = "",
    action_requested: str = "review"
) -> str:
    instance_name = os.getenv("ACTIVE_INSTANCE", "anonymous_agent")
    try:
        disp = send_dispatch(
            sender_instance=instance_name,
            recipient_instance_or_guild=recipient,
            subject=subject,
            body=body,
            reference_node_id=reference_node_id,
            action_requested=action_requested
        )
        return f"Dispatch [{disp['dispatch_id']}] sent to '{recipient}' successfully."
    except Exception as e:
        return f"Error sending dispatch: {str(e)}"

def read_agent_inbox(unread_only: bool = False) -> str:
    instance_name = os.getenv("ACTIVE_INSTANCE", "anonymous_agent")
    try:
        inbox = read_inbox(instance_name, unread_only=unread_only)
        if not inbox:
            return "Inbox is empty. No active dispatches found."
        return json.dumps(inbox, indent=2)
    except Exception as e:
        return f"Error reading inbox: {str(e)}"

# --- WORKSPACE FILE & COMMAND TOOLS ---

def read_file(path: str) -> str:
    if not _is_safe_path(path):
        return "Error: Path is outside of allowed workspace."
    abs_path = _get_absolute_path(path)
    if not os.path.exists(abs_path):
        return f"Error: File {path} does not exist."
    if os.path.isdir(abs_path):
        return f"Error: '{path}' is a directory. Use run_command with 'dir' to list directory contents."
    
    # Handle binary files gracefully
    ext = os.path.splitext(abs_path)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.webp', '.ico']:
        file_size = os.path.getsize(abs_path)
        return f"[Binary Media File: '{path}', Size: {file_size} bytes]. Binary image files cannot be read as raw UTF-8 text. To inspect simulation data, review the accompanying python script or markdown report."

    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(path: str, content: str) -> str:
    if not _is_safe_path(path):
        return "Error: Path is outside of allowed workspace."
    abs_path = _get_absolute_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    try:
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def edit_file(path: str, old_content: str, new_content: str) -> str:
    if not _is_safe_path(path):
        return "Error: Path is outside of allowed workspace."
    abs_path = _get_absolute_path(path)
    if not os.path.exists(abs_path):
        return f"Error: File {path} does not exist."
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            file_data = f.read()
        if old_content not in file_data:
            return "Error: The exact search content (old_content) was not found in the file."
        if file_data.count(old_content) > 1:
            return "Error: Multiple occurrences of old_content found. Provide more surrounding context lines."
        updated = file_data.replace(old_content, new_content)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(updated)
        return f"Successfully edited file {path}."
    except Exception as e:
        return f"Error editing file: {str(e)}"

def run_command(command: str) -> str:
    try:
        p = subprocess.Popen(
            command,
            shell=True,
            cwd=get_workspace_dir(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            stdout, stderr = p.communicate(timeout=20)
            output = stdout or ""
            if stderr:
                output += f"\nSTDERR:\n{stderr}"
            return output if output else "Command executed silently."
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":
                subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
            p.kill()
            stdout, stderr = p.communicate()
            return "Error: Command execution timed out (exceeded 20 seconds)."
    except Exception as e:
        return f"Error running command: {str(e)}"

class DDGHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.in_title = False
        self.in_snippet = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get('class', '').split()
        if tag == 'a' and 'result__a' in classes:
            href = attrs_dict.get('href', '')
            if href.startswith('//duckduckgo.com/l/?uddg='):
                href = href.replace('//duckduckgo.com/l/?uddg=', '')
            elif href.startswith('/l/?uddg='):
                href = href.replace('/l/?uddg=', '')
            if 'uddg=' in href or 'uddg' in href:
                parsed = urllib.parse.urlparse(href)
                qs = urllib.parse.parse_qs(parsed.query)
                if 'uddg' in qs:
                    href = qs['uddg'][0]
            href = urllib.parse.unquote(href)
            if href.startswith('//'):
                href = 'https:' + href
            self.results.append({'title': '', 'href': href, 'body': ''})
            self.in_title = True
        elif tag == 'a' and 'result__snippet' in classes:
            self.in_snippet = True

    def handle_endtag(self, tag):
        if tag == 'a':
            self.in_title = False
            self.in_snippet = False

    def handle_data(self, data):
        if not self.results:
            return
        if self.in_title:
            self.results[-1]['title'] += data
        elif self.in_snippet:
            self.results[-1]['body'] += data

def search_web(query: str) -> str:
    try:
        url = 'https://html.duckduckgo.com/html/?' + urllib.parse.urlencode({'q': query})
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            parser = DDGHTMLParser()
            parser.feed(html)
            valid_results = []
            for r in parser.results:
                r['title'] = ' '.join(r['title'].split())
                r['body'] = ' '.join(r['body'].split())
                if r['title'] and r['href']:
                    valid_results.append(r)
            return json.dumps(valid_results[:5], indent=2)
    except Exception as e:
        return f"Error searching the web: {str(e)}"

# --- OPENAI / OPENROUTER TOOLS SCHEMA ---

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "post_epistemic_node",
            "description": "Publishes a new hypothesis, empirical trial, proof, critique, synthesis, or verified theorem to the shared Living Epistemic DAG.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Concise, descriptive title for this discovery/thesis"},
                    "node_type": {
                        "type": "string",
                        "enum": ["hypothesis", "empirical_test", "formal_proof", "critique", "synthesis", "canon_theorem"],
                        "description": "The epistemic role of this node"
                    },
                    "summary": {"type": "string", "description": "Core thesis, mathematical formulation, or synthesis explanation"},
                    "artifact_path": {"type": "string", "description": "Path to the generated code script, chart (.png), or report in shared_agora/artifacts/"},
                    "parents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of parent node IDs that this node extends, tests, or synthesizes"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Domain tags (e.g. ['chaos_theory', 'cellular_automata', 'resonance'])"
                    },
                    "confidence": {"type": "number", "description": "Self-calibrated confidence score between 0.0 and 1.0"}
                },
                "required": ["title", "node_type", "summary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "peer_verify_node",
            "description": "Performs formal peer verification (endorse, refute, or review) on a node created by another agent to contribute to cross-model quorum consensus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "The ID of the node to verify (e.g. 'HYP-001')"},
                    "verdict": {"type": "string", "enum": ["endorse", "refute", "inconclusive"], "description": "Your formal verdict"},
                    "critique_notes": {"type": "string", "description": "Detailed reasoning, edge-case test results, or replication logs"},
                    "confidence": {"type": "number", "description": "Confidence score in your verdict between 0.0 and 1.0"},
                    "reproduced_artifact_path": {"type": "string", "description": "Optional path to your replication script or chart"}
                },
                "required": ["node_id", "verdict", "critique_notes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_epistemic_graph",
            "description": "Queries the shared Living Epistemic DAG to find theorems, hypotheses awaiting review, or domain specific threads.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Specific Node ID to look up (e.g. 'HYP-002')"},
                    "status": {"type": "string", "enum": ["UNVERIFIED_HYPOTHESIS", "UNDER_REVIEW", "CANON_VERIFIED", "REFUTED"], "description": "Filter by status"},
                    "tag": {"type": "string", "description": "Filter by keyword tag"},
                    "node_type": {"type": "string", "description": "Filter by node type"},
                    "search_text": {"type": "string", "description": "Free text search in titles, summaries, node IDs, and tags"},
                    "limit": {"type": "integer", "description": "Maximum number of results to return"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_agent_dispatch",
            "description": "Sends a direct structured dispatch to another agent instance, a guild (e.g., 'guild:The Architects'), or broadcast to all.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Instance name (e.g. 'claude_haiku'), 'guild:The Architects', or 'broadcast'"},
                    "subject": {"type": "string", "description": "Subject of the message"},
                    "body": {"type": "string", "description": "Message content or collaboration request"},
                    "reference_node_id": {"type": "string", "description": "Associated DAG Node ID if referencing an existing proposition"},
                    "action_requested": {"type": "string", "enum": ["review", "replicate", "extend", "falsify", "info"], "description": "Action requested from recipient"}
                },
                "required": ["recipient", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_agent_inbox",
            "description": "Checks your agent inbox for incoming dispatches and collaboration requests from other models.",
            "parameters": {
                "type": "object",
                "properties": {
                    "unread_only": {"type": "boolean", "description": "If true, only returns unread dispatches"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads file contents from your local workspace or shared Agora directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes or overwrites a file in your workspace or in shared_agora/artifacts/.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"},
                    "content": {"type": "string", "description": "Content of the file"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replaces old_content with new_content in an existing file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"},
                    "old_content": {"type": "string", "description": "Exact text to replace"},
                    "new_content": {"type": "string", "description": "Replacement text"}
                },
                "required": ["path", "old_content", "new_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Executes a shell command in your workspace (run python scripts, generate plots, test code).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "PowerShell command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Searches external web sources for mathematical papers, scientific algorithms, or empirical reference data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    }
]

AVAILABLE_TOOLS = {
    "post_epistemic_node": post_epistemic_node,
    "peer_verify_node": peer_verify_node,
    "query_epistemic_graph": query_epistemic_graph,
    "send_agent_dispatch": send_agent_dispatch,
    "read_agent_inbox": read_agent_inbox,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "run_command": run_command,
    "search_web": search_web
}
