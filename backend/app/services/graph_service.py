import os
import json
from typing import Dict, List, Optional, Any, Set
import networkx as nx

GRAPHS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "graphs"
)

# In-memory graph cache: repo_name -> nx.DiGraph
_GRAPH_CACHE: Dict[str, nx.DiGraph] = {}


def _get_graph_file_path(repo_name: str) -> str:
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    safe_name = repo_name.replace("/", "_").replace("\\", "_")
    return os.path.join(GRAPHS_DIR, f"{safe_name}.json")


def _rel_path_from_full(file_path: str, repo_name: str) -> str:
    norm = file_path.replace("\\", "/")
    if f"/repositories/{repo_name}/" in norm:
        return norm.split(f"/repositories/{repo_name}/")[-1]
    if "/repositories/" in norm:
        after = norm.split("/repositories/")[-1]
        parts = after.split("/", 1)
        return parts[1] if len(parts) > 1 else os.path.basename(norm)
    return os.path.basename(norm)


def build_repository_graph(parsed_files: List[Dict[str, Any]], repo_name: str) -> nx.DiGraph:
    """
    Construct a comprehensive structural relationship graph using NetworkX.
    Captures:
    - Modules, Classes, Functions, and Methods (Nodes)
    - Containment: Module -> Class/Function, Class -> Method
    - Inheritance: Subclass -> Base Class
    - Function Calls: Caller -> Callee (with call site lines)
    - Module Imports: Importer Module -> Imported Module/Symbol
    """
    G = nx.DiGraph()
    G.graph["repository"] = repo_name

    # Symbol indexes for ultra-fast O(1) resolution:
    # symbol_name -> list of node_ids defining that symbol
    symbol_index: Dict[str, List[str]] = {}
    file_symbol_index: Dict[str, Dict[str, str]] = {}  # rel_path -> {symbol: node_id}

    # STEP 1: Add all entity nodes (Modules, Classes, Functions, Methods)
    for parsed in parsed_files:
        full_path = parsed.get("file", "")
        rel_path = _rel_path_from_full(full_path, repo_name)
        mod_node_id = f"mod::{rel_path}"

        G.add_node(
            mod_node_id,
            id=mod_node_id,
            type="module",
            name=os.path.basename(rel_path),
            rel_path=rel_path,
            full_path=full_path,
            docstring=""
        )

        file_symbol_index[rel_path] = {}

        # Add Classes
        for cls in parsed.get("classes", []):
            cls_name = cls["name"]
            cls_node_id = f"cls::{rel_path}::{cls_name}"
            docstring = cls.get("docstring", "")
            bases = cls.get("bases", [])

            G.add_node(
                cls_node_id,
                id=cls_node_id,
                type="class",
                name=cls_name,
                rel_path=rel_path,
                start_line=cls.get("line", 1),
                end_line=cls.get("end_line", 1),
                docstring=docstring,
                bases=bases
            )
            # Edge: Module contains Class
            G.add_edge(mod_node_id, cls_node_id, relation="CONTAINS")

            # Register in symbol index
            symbol_index.setdefault(cls_name, []).append(cls_node_id)
            file_symbol_index[rel_path][cls_name] = cls_node_id

        # Add Functions & Methods
        for fn in parsed.get("functions", []):
            fn_name = fn["name"]
            parent_cls = fn.get("parent_class")
            if parent_cls:
                fn_type = "method"
                full_fn_name = f"{parent_cls}.{fn_name}"
                fn_node_id = f"fn::{rel_path}::{parent_cls}::{fn_name}"
            else:
                fn_type = "function"
                full_fn_name = fn_name
                fn_node_id = f"fn::{rel_path}::{fn_name}"

            docstring = fn.get("docstring", "")
            args = fn.get("args", [])

            G.add_node(
                fn_node_id,
                id=fn_node_id,
                type=fn_type,
                name=fn_name,
                full_name=full_fn_name,
                parent_class=parent_cls,
                rel_path=rel_path,
                start_line=fn.get("line", 1),
                end_line=fn.get("end_line", 1),
                docstring=docstring,
                args=args
            )

            if parent_cls:
                cls_node_id = f"cls::{rel_path}::{parent_cls}"
                if G.has_node(cls_node_id):
                    G.add_edge(cls_node_id, fn_node_id, relation="CONTAINS")
                else:
                    G.add_edge(mod_node_id, fn_node_id, relation="CONTAINS")
            else:
                G.add_edge(mod_node_id, fn_node_id, relation="CONTAINS")

            # Register in symbol index
            symbol_index.setdefault(fn_name, []).append(fn_node_id)
            symbol_index.setdefault(full_fn_name, []).append(fn_node_id)
            file_symbol_index[rel_path][fn_name] = fn_node_id
            if parent_cls:
                file_symbol_index[rel_path][full_fn_name] = fn_node_id

    # STEP 2: Add Class Inheritance Edges
    for parsed in parsed_files:
        rel_path = _rel_path_from_full(parsed.get("file", ""), repo_name)
        for cls in parsed.get("classes", []):
            cls_name = cls["name"]
            cls_node_id = f"cls::{rel_path}::{cls_name}"
            for base in cls.get("bases", []):
                # Resolve base class
                target_node_id = None
                # Check local file first
                if base in file_symbol_index.get(rel_path, {}):
                    target_node_id = file_symbol_index[rel_path][base]
                elif base in symbol_index:
                    target_node_id = symbol_index[base][0]
                
                if target_node_id:
                    G.add_edge(cls_node_id, target_node_id, relation="INHERITS_FROM", base=base)
                else:
                    # External or standard library base class (e.g. object, Exception)
                    external_node = f"ext::{base}"
                    if not G.has_node(external_node):
                        G.add_node(external_node, id=external_node, type="external_class", name=base)
                    G.add_edge(cls_node_id, external_node, relation="INHERITS_FROM", base=base)

    # STEP 3: Add Imports Edges
    for parsed in parsed_files:
        rel_path = _rel_path_from_full(parsed.get("file", ""), repo_name)
        mod_node_id = f"mod::{rel_path}"

        for imp in parsed.get("imports", []):
            mod_target = imp.get("module")
            imported_names = imp.get("names", [])
            line = imp.get("line", 1)

            if mod_target:
                # Try matching known module rel_paths
                target_mod_id = None
                for candidate_path in file_symbol_index:
                    if candidate_path.replace(".py", "").endswith(mod_target.replace(".", "/")) or \
                       candidate_path.replace(".py", "").replace("/", ".") == mod_target:
                        target_mod_id = f"mod::{candidate_path}"
                        break

                if target_mod_id and G.has_node(target_mod_id):
                    G.add_edge(mod_node_id, target_mod_id, relation="IMPORTS", line=line, names=imported_names)
                else:
                    ext_mod_id = f"ext_mod::{mod_target}"
                    if not G.has_node(ext_mod_id):
                        G.add_node(ext_mod_id, id=ext_mod_id, type="external_module", name=mod_target)
                    G.add_edge(mod_node_id, ext_mod_id, relation="IMPORTS", line=line, names=imported_names)

    # STEP 4: Add Function Call Edges (Caller -> Callee)
    for parsed in parsed_files:
        rel_path = _rel_path_from_full(parsed.get("file", ""), repo_name)

        # File-level functions/methods with their scoped calls
        for fn in parsed.get("functions", []):
            fn_name = fn["name"]
            parent_cls = fn.get("parent_class")
            if parent_cls:
                caller_id = f"fn::{rel_path}::{parent_cls}::{fn_name}"
            else:
                caller_id = f"fn::{rel_path}::{fn_name}"

            if not G.has_node(caller_id):
                continue

            for call in fn.get("calls", []):
                callee_name = call.get("name")
                call_line = call.get("line")
                if not callee_name:
                    continue

                # Resolve callee node
                target_node = None
                # Check current file first
                if callee_name in file_symbol_index.get(rel_path, {}):
                    target_node = file_symbol_index[rel_path][callee_name]
                # Check repo-wide
                elif callee_name in symbol_index:
                    # Pick most appropriate definition
                    candidates = symbol_index[callee_name]
                    target_node = candidates[0]

                if target_node and target_node != caller_id:
                    G.add_edge(caller_id, target_node, relation="CALLS", line=call_line, name=callee_name)

    # Cache in memory
    _GRAPH_CACHE[repo_name] = G
    save_graph(repo_name, G)
    return G


def save_graph(repo_name: str, G: nx.DiGraph) -> str:
    """Save graph to JSON node-link format for fast persistence."""
    path = _get_graph_file_path(repo_name)
    data = nx.node_link_data(G)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_graph(repo_name: str) -> Optional[nx.DiGraph]:
    """Load graph from JSON node-link format into NetworkX DiGraph."""
    if repo_name in _GRAPH_CACHE:
        return _GRAPH_CACHE[repo_name]

    path = _get_graph_file_path(repo_name)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        G = nx.node_link_graph(data)
        _GRAPH_CACHE[repo_name] = G
        return G
    except Exception as e:
        print(f"Error loading graph for {repo_name}: {e}")
        return None


def get_or_load_graph(repo_name: str) -> Optional[nx.DiGraph]:
    return _GRAPH_CACHE.get(repo_name) or load_graph(repo_name)


def expand_structural_context(
    repo_name: str,
    retrieved_chunks: List[Dict[str, Any]],
    max_hops: int = 1
) -> Dict[str, Any]:
    """
    Perform 1-hop / 2-hop structural graph expansion around retrieved code chunks.
    Identifies:
    - Who calls these functions (Callers)
    - Which functions they call (Callees)
    - What class hierarchy they belong to (Inheritance / Methods)
    - Imported dependencies
    """
    G = get_or_load_graph(repo_name)
    if G is None or len(G.nodes) == 0:
        return {
            "has_graph": False,
            "relationships": [],
            "expanded_nodes": [],
            "graph_summary": "Graph not available for repository."
        }

    matched_nodes: Set[str] = set()

    for chunk in retrieved_chunks:
        c_name = chunk.get("name", "")
        c_file = chunk.get("rel_path") or os.path.basename(chunk.get("file", ""))
        c_type = chunk.get("type", "")

        # Try exact node lookup
        for node_id, attrs in G.nodes(data=True):
            if attrs.get("name") == c_name or attrs.get("full_name") == c_name:
                node_rel = attrs.get("rel_path", "")
                if not c_file or c_file in node_rel or node_rel in c_file:
                    matched_nodes.add(node_id)

        # Fallback by name only
        if not matched_nodes:
            for node_id, attrs in G.nodes(data=True):
                if attrs.get("name") == c_name:
                    matched_nodes.add(node_id)

    relationships: List[str] = []
    expanded_nodes: List[Dict[str, Any]] = []
    seen_expanded: Set[str] = set(matched_nodes)

    for node_id in matched_nodes:
        node_data = G.nodes[node_id]
        node_name = node_data.get("full_name") or node_data.get("name", node_id)
        node_file = node_data.get("rel_path", "")

        # 1. Outgoing edges: CALLEES, INHERITS_FROM, CONTAINS
        for _, target_id, edge_data in G.out_edges(node_id, data=True):
            rel = edge_data.get("relation", "")
            target_data = G.nodes.get(target_id, {})
            target_name = target_data.get("full_name") or target_data.get("name", target_id)
            target_file = target_data.get("rel_path", "")

            if rel == "CALLS":
                relationships.append(f"`{node_name}` calls `{target_name}` ({target_file})")
            elif rel == "INHERITS_FROM":
                relationships.append(f"`{node_name}` inherits from `{target_name}`")
            elif rel == "CONTAINS" and target_data.get("type") == "method":
                relationships.append(f"`{node_name}` contains method `{target_name}`")

            if target_id not in seen_expanded:
                seen_expanded.add(target_id)
                expanded_nodes.append({
                    "id": target_id,
                    "name": target_name,
                    "type": target_data.get("type", "unknown"),
                    "file": target_file,
                    "line": target_data.get("start_line", 0),
                    "end_line": target_data.get("end_line", 0),
                    "docstring": target_data.get("docstring", ""),
                    "relation": f"Called/Target of {node_name}"
                })

        # 2. Incoming edges: CALLERS (who calls this node?)
        for source_id, _, edge_data in G.in_edges(node_id, data=True):
            rel = edge_data.get("relation", "")
            source_data = G.nodes.get(source_id, {})
            source_name = source_data.get("full_name") or source_data.get("name", source_id)
            source_file = source_data.get("rel_path", "")

            if rel == "CALLS":
                relationships.append(f"`{node_name}` is called by `{source_name}` ({source_file})")
            elif rel == "INHERITS_FROM":
                relationships.append(f"`{source_name}` is a subclass of `{node_name}`")
            elif rel == "CONTAINS" and source_data.get("type") == "class":
                relationships.append(f"`{node_name}` is defined in class `{source_name}` ({source_file})")

            if source_id not in seen_expanded:
                seen_expanded.add(source_id)
                expanded_nodes.append({
                    "id": source_id,
                    "name": source_name,
                    "type": source_data.get("type", "unknown"),
                    "file": source_file,
                    "line": source_data.get("start_line", 0),
                    "end_line": source_data.get("end_line", 0),
                    "docstring": source_data.get("docstring", ""),
                    "relation": f"Caller/Parent of {node_name}"
                })

    # Summary string for LLM prompt context injection
    summary_lines = []
    if relationships:
        summary_lines.append("Codebase Structural Graph Relationships:")
        for r in relationships[:12]:
            summary_lines.append(f"- {r}")

    return {
        "has_graph": True,
        "matched_nodes": list(matched_nodes),
        "relationships": relationships[:20],
        "expanded_nodes": expanded_nodes[:10],
        "graph_summary": "\n".join(summary_lines)
    }


def get_graph_visualization_data(repo_name: str, max_nodes: int = 120) -> Dict[str, Any]:
    """
    Export nodes and edges formatted for React graph visualization / UI inspection.
    """
    G = get_or_load_graph(repo_name)
    if G is None:
        return {"nodes": [], "edges": [], "stats": {"nodes": 0, "edges": 0}}

    # Prioritize functions, methods, and classes over external modules
    scored_nodes = []
    for n, d in G.nodes(data=True):
        ntype = d.get("type", "")
        degree = G.degree(n)
        weight = degree * (3 if ntype in ("function", "method", "class") else 1)
        scored_nodes.append((weight, n))

    scored_nodes.sort(reverse=True, key=lambda x: x[0])
    selected_nodes = set(n for _, n in scored_nodes[:max_nodes])

    vis_nodes = []
    for n in selected_nodes:
        d = G.nodes[n]
        vis_nodes.append({
            "id": n,
            "label": d.get("name") or n,
            "type": d.get("type", "node"),
            "file": d.get("rel_path", ""),
            "line": d.get("start_line", 0),
            "docstring": (d.get("docstring") or "")[:150]
        })

    vis_edges = []
    for u, v, d in G.edges(data=True):
        if u in selected_nodes and v in selected_nodes:
            vis_edges.append({
                "source": u,
                "target": v,
                "relation": d.get("relation", "CONNECTS")
            })

    return {
        "nodes": vis_nodes,
        "edges": vis_edges,
        "stats": {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "rendered_nodes": len(vis_nodes),
            "rendered_edges": len(vis_edges)
        }
    }


def get_graph_statistics(repo_name: str) -> Dict[str, Any]:
    """Return topological stats about repository structure."""
    G = get_or_load_graph(repo_name)
    if G is None:
        return {"available": False}

    node_types: Dict[str, int] = {}
    for _, d in G.nodes(data=True):
        t = d.get("type", "other")
        node_types[t] = node_types.get(t, 0) + 1

    in_degrees = sorted(G.in_degree(), key=lambda x: x[1], reverse=True)
    top_called = [
        {"node": G.nodes[n].get("name", n), "calls_count": deg, "file": G.nodes[n].get("rel_path", "")}
        for n, deg in in_degrees[:5] if G.nodes[n].get("type") in ("function", "method") and deg > 0
    ]

    return {
        "available": True,
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "node_types": node_types,
        "top_referenced_functions": top_called
    }
