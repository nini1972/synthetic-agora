import os
import sys
import subprocess
import signal
import json
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from typing import Any, Optional, Dict, List, Union
from agora_graph import EpistemicGraph, get_shared_agora_dir
from protocols import send_dispatch, read_inbox
from embassy import export_treaty_to_embassy as _export_treaty_to_embassy

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
    if norm_path.startswith("world_c/"):
        return os.path.abspath(os.path.join(shared, norm_path))
    
    target = os.path.abspath(os.path.join(workspace, path_str))
    if not os.path.exists(target):
        # Check in local world_c_results
        ws_res = os.path.abspath(os.path.join(workspace, "world_c_results", os.path.basename(path_str)))
        if os.path.exists(ws_res):
            return ws_res
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
        # Check in shared world_c reports
        shared_report = os.path.abspath(os.path.join(shared, "world_c", "reports", os.path.basename(path_str)))
        if os.path.exists(shared_report):
            return shared_report
        # Check in shared world_c artifacts
        shared_art_wc = os.path.abspath(os.path.join(shared, "world_c", "artifacts", os.path.basename(path_str)))
        if os.path.exists(shared_art_wc):
            return shared_art_wc
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
    confidence: float = 0.85,
    parent: Any = None,
    **kwargs
) -> str:
    instance_name = os.getenv("ACTIVE_INSTANCE", "anonymous_agent")
    if parent is not None and not parents:
        parents = [parent] if isinstance(parent, str) else list(parent)
    
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

def export_treaty_to_embassy(node_id: str, originating_dossier_filename: str = "") -> str:
    """Deposits a formal Ratified Epistemic Treaty into embassy/outbox/ for a CANON_VERIFIED node."""
    try:
        return _export_treaty_to_embassy(node_id, originating_dossier_filename)
    except Exception as e:
        return f"Error exporting treaty to embassy: {str(e)}"

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

def run_command(command: str = "", **kwargs) -> str:
    if not command:
        command = kwargs.get("cmd") or kwargs.get("script") or kwargs.get("code") or ""
    if not command:
        return "Error: No command provided to run."
    try:
        # On POSIX (Linux), use start_new_session=True so child processes can be killed as a group
        popen_kwargs = {
            "cwd": get_workspace_dir(),
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True
        }
        if sys.platform != "win32":
            popen_kwargs["start_new_session"] = True
            
        p = subprocess.Popen(command, shell=True, **popen_kwargs)
        try:
            stdout, stderr = p.communicate(timeout=60)
            output = stdout or ""
            if stderr:
                output += f"\nSTDERR:\n{stderr}"
            return output if output else "Command executed silently."
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":
                subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
            else:
                try:
                    os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                except Exception:
                    p.kill()
            try:
                stdout, stderr = p.communicate(timeout=2)
            except Exception:
                pass
            return "Error: Command execution timed out (exceeded 60 seconds). Optimize your simulation or reduce loop iterations."
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

def submit_world_c_job(title: str, script_content: str, timeout_seconds: int = 3600, parameters: dict = None) -> str:
    """
    Submits a heavy computation or simulation job to World C (the high-performance compute substrate).
    World C executes the job asynchronously without being killed by turn timeout limits,
    has access to colony_lib (Kuramoto, Solitons, Gray-Scott, RQA, Bifurcations, Morphospace),
    and returns artifacts (plots, JSON metrics) and an execution report back to instances/shared_agora/world_c/reports/ and your local world_c_results/.
    """
    import uuid
    import time
    
    instance_name = os.getenv("ACTIVE_INSTANCE", "agora_citizen")
    job_id = f"job_{instance_name}_{int(time.time())}_{uuid.uuid4().hex[:4]}"
    
    shared_space = get_shared_agora_dir()
    os.makedirs(shared_space, exist_ok=True)
    req_file = os.path.join(shared_space, f"{job_id}_job_request.json")
    
    payload = {
        "job_id": job_id,
        "title": title,
        "lineage_author": instance_name,
        "realm_source": "world_b",
        "script_content": script_content,
        "parameters": parameters or {},
        "timeout_seconds": timeout_seconds
    }
    
    try:
        with open(req_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        return f"Error submitting job request: {e}"
        
    bridge_msg = ""
    try:
        candidate_dirs = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "world_c")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "world_c")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "world_c")),
            r"C:\Users\ninic\.gemini\antigravity\scratch\world_c"
        ]
        world_c_dir = None
        for cd in candidate_dirs:
            if os.path.exists(cd) and os.path.exists(os.path.join(cd, "embassy", "bridge.py")):
                world_c_dir = cd
                break

        if world_c_dir:
            if world_c_dir not in sys.path:
                sys.path.insert(0, world_c_dir)
            import importlib.util
            bridge_path = os.path.join(world_c_dir, "embassy", "bridge.py")
            spec_mod = importlib.util.spec_from_file_location("world_c_embassy_bridge", bridge_path)
            mod = importlib.util.module_from_spec(spec_mod)
            spec_mod.loader.exec_module(mod)
            bridge = mod.EmbassyBridge(
                world_b_root=os.path.abspath(os.path.dirname(__file__)),
                world_c_root=world_c_dir
            )
            bridge.scan_and_process_inbox(auto_execute=True, async_mode=True)
            bridge_msg = " [World C Embassy Bridge automatically dispatched the job asynchronously!]"
    except Exception as e:
        bridge_msg = f" [Queued in shared_agora; background bridge will process: {e}]"
        
    return f"Job '{job_id}' ('{title}') successfully registered for World C! Artifacts and execution report will be delivered to 'instances/shared_agora/world_c/reports/' and your local 'world_c_results/' directory upon completion.{bridge_msg}"

def check_world_c_job(job_id: str) -> str:
    """
    Checks the status and results of a submitted World C compute job.
    Returns status, compute duration, generated artifacts, and execution log summary.
    """
    workspace = get_workspace_dir()
    shared = get_shared_agora_dir()
    
    # 1. Check workspace results first
    ws_report = os.path.join(workspace, "world_c_results", f"world_c_{job_id}_REPORT.md")
    if os.path.exists(ws_report):
        with open(ws_report, "r", encoding="utf-8") as f:
            return f.read()

    # Check generic REPORT.md only if it contains the matching job_id
    ws_generic = os.path.join(workspace, "world_c_results", "REPORT.md")
    if os.path.exists(ws_generic):
        try:
            with open(ws_generic, "r", encoding="utf-8") as f:
                content = f.read()
                if job_id in content:
                    return content
        except Exception:
            pass

    # 2. Check dedicated world_c reports in shared_agora
    dedicated_report = os.path.join(shared, "world_c", "reports", f"world_c_{job_id}_REPORT.md")
    if os.path.exists(dedicated_report):
        with open(dedicated_report, "r", encoding="utf-8") as f:
            return f.read()

    # 3. Check legacy shared_agora root report
    legacy_report = os.path.join(shared, f"world_c_{job_id}_REPORT.md")
    if os.path.exists(legacy_report):
        with open(legacy_report, "r", encoding="utf-8") as f:
            return f.read()

    # 4. Check World C internal jobs directory if available
    world_c_candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "world_c")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "world_c")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "world_c")),
        r"C:\Users\ninic\.gemini\antigravity\scratch\world_c"
    ]
    world_c_dir = None
    for cd in world_c_candidates:
        if os.path.exists(cd) and os.path.exists(os.path.join(cd, "jobs")):
            world_c_dir = cd
            break

    if world_c_dir:
        job_dir = os.path.join(world_c_dir, "jobs", job_id)
        job_result_path = os.path.join(job_dir, "result.json")
        if os.path.exists(job_result_path):
            try:
                with open(job_result_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                status = data.get("status", "UNKNOWN")

                # If completed or failed, ensure artifacts and reports are published
                if status in ["COMPLETED", "FAILED"]:
                    try:
                        if world_c_dir not in sys.path:
                            sys.path.insert(0, world_c_dir)
                        from embassy.bridge import EmbassyBridge
                        from compute_engine.job_spec import JobSpec
                        bridge = EmbassyBridge(
                            world_b_root=os.path.abspath(os.path.dirname(__file__)),
                            world_c_root=world_c_dir
                        )
                        spec_p = os.path.join(job_dir, "spec.json")
                        if os.path.exists(spec_p):
                            with open(spec_p, "r", encoding="utf-8") as sf:
                                spec_data = json.load(sf)
                            res = bridge.dispatcher.get_result(job_id)
                            if res:
                                bridge.publish_completed_artifacts(job_id, target_realms=["world_b"], lineage_author=spec_data.get("lineage_author"))
                                bridge.write_completion_report(res, JobSpec(**spec_data), destination_dir=os.path.join(shared, "world_c", "reports"))
                                if os.path.exists(ws_report):
                                    with open(ws_report, "r", encoding="utf-8") as rf:
                                        return rf.read()
                    except Exception:
                        pass

                return f"Job '{job_id}' status: {status}. Execution time: {data.get('execution_time_seconds', 0):.2f}s. Artifacts: {data.get('artifacts_generated', [])}."
            except Exception:
                pass

    # 5. Check if still queued
    req_file = os.path.join(shared, f"{job_id}_job_request.json")
    if os.path.exists(req_file):
        return f"Job '{job_id}' is currently QUEUED and awaiting execution."

    return f"Job '{job_id}' not found yet. It may still be executing or initializing. Check 'instances/shared_agora/world_c/reports/' shortly."

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
                    "command": {"type": "string", "description": "Shell command to execute (e.g. 'python script.py', 'ls -la')"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_treaty_to_embassy",
            "description": "Deposits a formal Ratified Epistemic Treaty into embassy/outbox/ for a CANON_VERIFIED graph node, so it can be synced back to World A (the Frontier). Refuses to run on nodes that are not yet CANON_VERIFIED or lack cross-family quorum.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "The CANON_VERIFIED node ID to export as a treaty (e.g. 'EMP-004')"},
                    "originating_dossier_filename": {"type": "string", "description": "Filename of the Frontier dossier this canon node traces back to, if any (e.g. 'DOSSIER-evosandbox-2026-09-01-kuramoto.md'). Leave empty if the node originated within the Agora itself."}
                },
                "required": ["node_id"]
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
    },
    {
        "type": "function",
        "function": {
            "name": "submit_world_c_job",
            "description": "Submits a heavy computation or simulation job to World C (the high-performance compute substrate). World C executes the job asynchronously without being killed by turn timeout limits, has access to colony_lib (Kuramoto, Solitons, Gray-Scott, RQA, Bifurcations, Morphospace), and returns artifacts (plots, JSON metrics) and an execution report back to instances/shared_agora/world_c/reports/ and your local world_c_results/.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short title describing the experiment."},
                    "script_content": {"type": "string", "description": "The complete Python script to execute in World C."},
                    "timeout_seconds": {"type": "integer", "description": "Execution timeout in seconds (default: 3600)."},
                    "parameters": {"type": "object", "description": "Optional dictionary of parameter configurations."}
                },
                "required": ["title", "script_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_world_c_job",
            "description": "Checks the execution status, logs, and artifacts of a submitted World C compute job.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "The unique job ID returned by submit_world_c_job."
                    }
                },
                "required": ["job_id"]
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
    "export_treaty_to_embassy": export_treaty_to_embassy,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "run_command": run_command,
    "shell": run_command,
    "bash": run_command,
    "terminal": run_command,
    "execute_command": run_command,
    "search_web": search_web,
    "submit_world_c_job": submit_world_c_job,
    "check_world_c_job": check_world_c_job
}
