import functools
import itertools
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from urllib import request

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from nmdc_server.database import create_session
from nmdc_server.models import Biosample, EnvoAncestor, EnvoTerm, EnvoTree
from nmdc_server.schemas import EnvoTreeNode

envo_url = "http://purl.obolibrary.org/obo/envo/subsets/envo-basic.json"


def populate_envo_ancestor(
    db: Session,
    term_id: str,
    node: str,
    edges: Dict[str, Set[str]],
    all_nodes: Set[str],
    direct: bool,
    visited: Set[str],
):
    if node in visited:
        raise Exception("Cyclic graph detected")
    if node not in edges:
        return
    visited = visited.union({node})
    for parent in edges[node]:
        if parent not in all_nodes:
            continue  # skip ancestors outside the simplified hierarchy

        statement = insert(EnvoAncestor.__table__).values(
            id=term_id, ancestor_id=parent, direct=direct
        )
        if direct:
            statement = statement.on_conflict_do_update(
                index_elements=["id", "ancestor_id"], set_={"direct": True}
            )
        else:
            statement = statement.on_conflict_do_nothing(index_elements=["id", "ancestor_id"])
        db.execute(statement)
    for parent in edges[node]:
        if parent not in all_nodes:
            continue  # skip ancestors outside the simplified hierarchy

        populate_envo_ancestor(db, term_id, parent, edges, all_nodes, False, visited)


def get_biosample_roots(db: Session) -> Dict[str, Set[str]]:
    """
    Find all reachable envo root terms from each biosample envo facet.

    Returns a dict mapping facet name to the set of reachable roots.
    """
    parents: Dict[str, str] = {}
    query = db.query(EnvoAncestor).filter(EnvoAncestor.direct.is_(True))
    for ancestor in query:
        parents[ancestor.id] = ancestor.ancestor_id

    def reachable_roots(attr: str) -> Set[str]:
        query = db.query(getattr(Biosample, attr)).distinct()
        terms = set(r[0] for r in query) - {None}
        roots = set()

        for term in terms:
            # traverse up the ancestors until reaching a root
            if term not in parents:
                roots.add(term)
            else:
                parent = parents[term]
                while parent in parents:
                    parent = parents[parent]
                roots.add(parent)
        return roots

    # TODO should we store these results in the database?
    return {
        key: reachable_roots(key)
        for key in ["env_broad_scale_id", "env_local_scale_id", "env_medium_id"]
    }


def _build_envo_subtree(db: Session, parent_id: str) -> None:
    query = (
        db.query(EnvoAncestor)
        .filter(EnvoAncestor.ancestor_id == parent_id)
        .filter(EnvoAncestor.direct.is_(True))
    )
    for node in query:
        statement = (
            insert(EnvoTree.__table__)
            .values(
                {
                    "id": node.id,
                    "parent_id": parent_id,
                }
            )
            .on_conflict_do_nothing()
        )
        db.execute(statement)

        _build_envo_subtree(db, node.id)


def build_envo_trees(db: Session) -> None:
    """
    Convert the envo_ancestors graph into trees, and store them (normalized).

    If a node is encountered more than once, we arbitrarily choose its first
    encountered location in the graph.

    This should only be called after biosamples have been ingested.
    """
    db.execute(f"truncate table {EnvoTree.__tablename__}")

    roots = get_biosample_roots(db)
    root_set = set(itertools.chain(*roots.values()))
    for root in root_set:
        statement = insert(EnvoTree.__table__).values(
            {
                "id": root,
                "parent_id": None,  # null parent_id indicates root node(s)
            }
        )
        db.execute(statement)

        _build_envo_subtree(db, root)

    db.commit()

    nested_envo_trees.cache_clear()


@dataclass
class _NodeInfo:
    id: str
    parent_id: str
    label: str
    visited: bool = False


TreeChildren = Dict[Optional[str], List[_NodeInfo]]  # envo id -> child node list


def _prune_subtree(tree_children: TreeChildren, node: _NodeInfo) -> None:
    tree_children[node.id] = [child for child in tree_children[node.id] if child.visited]
    for child in tree_children[node.id]:
        _prune_subtree(tree_children, child)


def _nested_envo_subtree(
    tree_children: TreeChildren, parent_id: Optional[str] = None
) -> List[EnvoTreeNode]:
    return [
        EnvoTreeNode(
            id=node.id,
            label=node.label,
            children=_nested_envo_subtree(tree_children, node.id),
        )
        for node in tree_children[parent_id]
    ]


@functools.lru_cache(maxsize=None)
def nested_envo_trees() -> Dict[str, List[EnvoTreeNode]]:
    tree_children = defaultdict(list)
    tree_nodes: Dict[str, _NodeInfo] = {}

    with create_session() as session:
        query = session.query(EnvoTerm, EnvoTree).filter(EnvoTerm.id == EnvoTree.id)
        for term, edge in query:
            node = _NodeInfo(id=edge.id, parent_id=edge.parent_id, label=term.label)
            tree_children[edge.parent_id].append(node)
            tree_nodes[edge.id] = node

        biosample_roots = get_biosample_roots(session)

        # Find all envo terms present in the biosamples
        broad_q = session.query(Biosample.env_broad_scale_id).distinct()
        local_q = session.query(Biosample.env_local_scale_id).distinct()
        medium_q = session.query(Biosample.env_medium_id).distinct()
        present_terms = set(r[0] for r in broad_q.union(local_q, medium_q)) - {None}

    # Mark all nodes that are reachable from the set of present terms
    for term in present_terms:
        node = tree_nodes[term]
        node.visited = True
        while node.parent_id is not None:
            node = tree_nodes[node.parent_id]
            node.visited = True

    # Remove all unreachable nodes
    for root in tree_children[None]:
        _prune_subtree(tree_children, root)

    # Recursively build the tree structure
    root_nodes = _nested_envo_subtree(tree_children)

    # Now awkwardly build the response object, mapping roots to the correct facets
    nested: Dict[str, List[EnvoTreeNode]] = {}
    for facet, roots in biosample_roots.items():
        nested[facet] = []
        for root_id in roots:
            for root_node in root_nodes:
                if root_node.id == root_id:
                    nested[facet].append(root_node)
                    break
    return nested


def load(db: Session):
    # TODO: might need to clear out old ancestor associations
    with request.urlopen(envo_url) as r:
        envo_data = json.load(r)

    for graph in envo_data["graphs"]:
        direct_ancestors: Dict[str, Set[str]] = defaultdict(set)
        for edge in graph["edges"]:
            if edge["pred"] != "is_a":
                continue

            id = edge["sub"].split("/")[-1].replace("_", ":")
            parent = edge["obj"].split("/")[-1].replace("_", ":")
            if id != parent:
                direct_ancestors[id].add(parent)

        ids: Set[str] = set()
        for node in graph["nodes"]:
            if not node["id"].startswith("http://purl.obolibrary.org/obo/"):
                continue

            id = node["id"].split("/")[-1].replace("_", ":")
            label = node.pop("lbl", "")
            data = node.get("meta", {})
            envo_data = dict(id=id, label=label, data=data)
            sql = insert(EnvoTerm.__table__).values(envo_data)
            db.execute(sql.on_conflict_do_update(constraint="pk_envo_term", set_=envo_data))
            ids.add(id)

        db.flush()

        for node in ids:
            ancestor_data = dict(id=node, ancestor_id=node, direct=False)
            sql = insert(EnvoAncestor.__table__).values(ancestor_data)
            db.execute(sql.on_conflict_do_nothing())
            db.flush()
            populate_envo_ancestor(db, node, node, direct_ancestors, ids, True, set())

    db.commit()
