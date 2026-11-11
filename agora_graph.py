import os
import sys
import re
import json
import time
import contextlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

@contextlib.contextmanager
def _graph_file_lock(lock_path: str, timeout: float = 30.0, poll_interval: float = 0.05):
    start = time.time()
    fd = None
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            break
        except (FileExistsError, OSError):
            if os.path.exists(lock_path):
                try:
                    mtime = os.path.getmtime(lock_path)
                    if time.time() - mtime > timeout:
                        # Break stale lock
                        try:
                            os.unlink(lock_path)
                        except OSError:
                            pass
                        continue
                except OSError:
                    pass
            if time.time() - start >= timeout:
                try:
                    os.unlink(lock_path)
                except OSError:
                    pass
                try:
                    fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    break
                except OSError:
                    pass
            time.sleep(poll_interval)
    try:
        yield
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            if os.path.exists(lock_path):
                os.unlink(lock_path)
        except OSError:
            pass

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def get_shared_agora_dir() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    shared = os.path.join(base_dir, "instances", "shared_agora")
    os.makedirs(shared, exist_ok=True)
    os.makedirs(os.path.join(shared, "artifacts"), exist_ok=True)
    os.makedirs(os.path.join(shared, "canon"), exist_ok=True)
    os.makedirs(os.path.join(shared, "dispatches"), exist_ok=True)
    return shared

def get_graph_path() -> str:
    return os.path.join(get_shared_agora_dir(), "knowledge_graph.json")

def detect_model_family(model_or_instance: str) -> str:
    s = model_or_instance.lower()
    if "claude" in s or "anthropic" in s:
        return "anthropic"
    elif "gemini" in s or "google" in s:
        return "google"
    elif "llama" in s or "meta" in s:
        return "meta"
    elif "kimi" in s or "moonshot" in s:
        return "moonshot"
    elif "deepseek" in s:
        return "deepseek"
    elif "minimax" in s:
        return "minimax"
    elif "glm" in s or "z-ai" in s or "chatglm" in s:
        return "z-ai"
    elif "qwen" in s or "alibaba" in s:
        return "qwen"
    elif "mistral" in s:
        return "mistral"
    elif "gpt" in s or "openai" in s:
        return "openai"
    elif "poolside" in s:
        return "poolside"
    elif "tencent" in s or "hy3" in s:
        return "tencent"
    elif "xiaomi" in s or "mimo" in s:
        return "xiaomi"
    elif "nvidia" in s or "nemotron" in s:
        return "nvidia"
    return "autonomous_mind"

class EpistemicGraph:
    def __init__(self):
        self.file_path = get_graph_path()
        self._load()

    @property
    def lock_path(self) -> str:
        return self.file_path + ".lock"

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.nodes: Dict[str, Dict[str, Any]] = data.get("nodes", {})
                    self.meta: Dict[str, Any] = data.get("meta", {
                        "created_at": utc_now_iso(),
                        "version": "1.0-agora",
                        "total_theorems_verified": 0
                    })
                    return
            except Exception as e:
                print(f"[AgoraGraph] Warning: Failed to load existing graph ({e}). Initializing empty.")
        
        self.nodes = {}
        self.meta = {
            "created_at": utc_now_iso(),
            "version": "1.0-agora",
            "total_theorems_verified": 0
        }
        self.save()

    def save(self):
        self.meta["updated_at"] = utc_now_iso()
        self.meta["total_nodes"] = len(self.nodes)
        self.meta["total_theorems_verified"] = sum(
            1 for n in self.nodes.values() if n.get("status") == "CANON_VERIFIED"
        )
        temp_path = self.file_path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump({"meta": self.meta, "nodes": self.nodes}, f, indent=2, ensure_ascii=False)
        if os.path.exists(self.file_path):
            os.replace(temp_path, self.file_path)
        else:
            os.rename(temp_path, self.file_path)

    def generate_node_id(self, node_type: str) -> str:
        prefix = {
            "hypothesis": "HYP",
            "empirical_test": "EMP",
            "formal_proof": "PRF",
            "critique": "CRT",
            "synthesis": "SYN",
            "canon_theorem": "THM"
        }.get(node_type, "NOD")

        max_num = 0
        pat = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
        for nid in self.nodes:
            m = pat.match(nid)
            if m:
                max_num = max(max_num, int(m.group(1)))
        num = max(max_num + 1, sum(1 for nid in self.nodes if nid.startswith(prefix)) + 1)
        while f"{prefix}-{num:03d}" in self.nodes:
            num += 1
        return f"{prefix}-{num:03d}"

    def post_node(
        self,
        title: str,
        node_type: str,
        author_instance: str,
        summary: str,
        artifact_path: str = "",
        parents: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        confidence: float = 0.85
    ) -> Dict[str, Any]:
        with _graph_file_lock(self.lock_path):
            self._load()
            norm_title = re.sub(r"\s+", " ", str(title).strip().lower())
            valid_parents = [p for p in (parents or []) if p in self.nodes]
            for existing_id, existing_node in self.nodes.items():
                if (
                    existing_node.get("author_instance") == author_instance
                    and existing_node.get("node_type") == node_type
                    and re.sub(r"\s+", " ", str(existing_node.get("title", "")).strip().lower()) == norm_title
                ):
                    if len(str(summary)) >= len(str(existing_node.get("summary", ""))):
                        existing_node["summary"] = summary
                    if artifact_path:
                        existing_node["artifact_path"] = artifact_path
                    if valid_parents:
                        existing_node["parents"] = list(dict.fromkeys((existing_node.get("parents") or []) + valid_parents))
                    if tags:
                        existing_node["tags"] = list(dict.fromkeys((existing_node.get("tags") or []) + list(tags)))
                    existing_node["confidence"] = round(float(confidence), 3)
                    existing_node["updated_at"] = utc_now_iso()
                    self._evaluate_quorum(existing_id)
                    self.save()
                    return existing_node

            node_id = self.generate_node_id(node_type)
            author_family = detect_model_family(author_instance)
            
            node = {
                "id": node_id,
                "title": title,
                "node_type": node_type,
                "author_instance": author_instance,
                "author_family": author_family,
                "summary": summary,
                "artifact_path": artifact_path,
                "parents": valid_parents,
                "tags": tags or [],
                "confidence": round(float(confidence), 3),
                "verifications": [],
                "status": "UNVERIFIED_HYPOTHESIS" if node_type == "hypothesis" else "UNDER_REVIEW",
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso()
            }

            if node_type == "canon_theorem" and len(valid_parents) >= 2:
                node["status"] = "UNDER_REVIEW"

            self.nodes[node_id] = node
            self._evaluate_quorum(node_id)
            self.save()

            # Atomic read-back confirmation
            if node_id not in self.nodes or self.nodes[node_id].get("title") != title:
                raise RuntimeError(f"Atomic read-back verification failed for node [{node_id}]")
            return node

    def peer_verify(
        self,
        node_id: str,
        verifier_instance: str,
        verdict: str,
        critique_notes: str,
        confidence: float = 0.9,
        reproduced_artifact_path: str = ""
    ) -> Dict[str, Any]:
        with _graph_file_lock(self.lock_path):
            self._load()
            if node_id not in self.nodes:
                raise ValueError(f"Node '{node_id}' does not exist in the Epistemic DAG.")
            
            node = self.nodes[node_id]
            verifier_family = detect_model_family(verifier_instance)

            verification_entry = {
                "verifier_instance": verifier_instance,
                "verifier_family": verifier_family,
                "verdict": verdict,
                "critique_notes": critique_notes,
                "confidence": round(float(confidence), 3),
                "reproduced_artifact_path": reproduced_artifact_path,
                "timestamp": utc_now_iso()
            }
            
            node["verifications"] = [
                v for v in node["verifications"] if v.get("verifier_instance") != verifier_instance
            ]
            node["verifications"].append(verification_entry)
            node["updated_at"] = utc_now_iso()

            self._evaluate_quorum(node_id)
            self.save()
            return node

    def _evaluate_quorum(self, node_id: str):
        node = self.nodes[node_id]
        verifications = node.get("verifications", [])
        
        endorsements = [v for v in verifications if v.get("verdict") == "endorse"]
        refutations = [v for v in verifications if v.get("verdict") == "refute"]
        
        endorsing_families = set(v.get("verifier_family") for v in endorsements)
        if node.get("confidence", 0) >= 0.8:
            endorsing_families.add(node.get("author_family"))
            
        refuting_families = set(v.get("verifier_family") for v in refutations)

        if refutations and len(refuting_families) >= 2:
            node["status"] = "REFUTED"
        elif len(endorsing_families) >= 2 and len(endorsements) >= 2:
            avg_conf = sum(v.get("confidence", 0.8) for v in endorsements) / len(endorsements)
            if avg_conf >= 0.75 and not refutations:
                node["status"] = "CANON_VERIFIED"
            else:
                node["status"] = "UNDER_REVIEW"
        elif len(verifications) > 0:
            node["status"] = "UNDER_REVIEW"

    def query(
        self,
        node_id: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        node_type: Optional[str] = None,
        author_family: Optional[str] = None,
        search_text: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        self._load()
        results = []
        for n in reversed(list(self.nodes.values())):
            if node_id and n.get("id", "").upper() != node_id.upper():
                continue
            if status and n.get("status") != status:
                continue
            if node_type and n.get("node_type") != node_type:
                continue
            if author_family and n.get("author_family") != author_family:
                continue
            if tag and tag.lower() not in [t.lower() for t in n.get("tags", [])]:
                continue
            if search_text:
                st = search_text.lower()
                text_blob = f"{n.get('id','')} {n.get('title','')} {n.get('summary','')} {' '.join(n.get('tags',[]))}".lower()
                if st not in text_blob:
                    continue
            results.append(n)
            if len(results) >= limit:
                break
        return results

    def get_summary_stats(self) -> Dict[str, Any]:
        self._load()
        status_counts = {}
        type_counts = {}
        family_contributions = {}

        for n in self.nodes.values():
            st = n.get("status", "UNKNOWN")
            status_counts[st] = status_counts.get(st, 0) + 1
            
            nt = n.get("node_type", "UNKNOWN")
            type_counts[nt] = type_counts.get(nt, 0) + 1
            
            fam = n.get("author_family", "unknown")
            family_contributions[fam] = family_contributions.get(fam, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "family_contributions": family_contributions,
            "canon_verified_count": status_counts.get("CANON_VERIFIED", 0)
        }
