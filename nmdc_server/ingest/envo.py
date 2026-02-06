import functools
import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from nmdc_server.database import SessionLocal
from nmdc_server.logger import get_logger
from nmdc_server.models import Biosample, EnvoAncestor, EnvoTerm, EnvoTree
from nmdc_server.schemas import EnvoTreeNode

logger = get_logger(__name__)


def load(db: Session) -> None:
    """Populate the EnvoTerm and EnvoAncestor tables from the generic ontology tables.

    Loads ALL terms from ontology_class (not just ENVO) to preserve the full hierarchy.
    The tree is filtered later to only show terms reachable from biosample env_* values.
    """
    logger.info("Populating EnvoTerm table from generic ontology data...")

    db.execute(text("DELETE FROM envo_ancestor"))

    # Upsert ALL terms from OntologyClass (ENVO, BFO, GO, UBERON, PO, etc.)
    upsert_all_terms_sql = """
    INSERT INTO envo_term (id, label, data)
    SELECT
        oc.id,
        oc.name as label,
        jsonb_build_object(
            'definition', COALESCE(oc.definition, ''),
            'alternative_names', oc.alternative_names,
            'is_obsolete', oc.is_obsolete,
            'is_root', oc.is_root,
            'annotations', oc.annotations
        ) as data
    FROM ontology_class oc
    ON CONFLICT (id) DO UPDATE SET
        label = EXCLUDED.label,
        data = EXCLUDED.data
    """
    db.execute(text(upsert_all_terms_sql))

    # Self-referential ancestors for faceted search
    insert_self_ancestors_sql = """
    INSERT INTO envo_ancestor (id, ancestor_id, direct)
    SELECT id, id, false
    FROM envo_term
    """
    db.execute(text(insert_self_ancestors_sql))

    # Direct parent relationships (rdfs:subClassOf only, not part_of)
    insert_direct_parents_sql = """
    INSERT INTO envo_ancestor (id, ancestor_id, direct)
    SELECT DISTINCT
        r.subject as id,
        r.object as ancestor_id,
        true as direct
    FROM ontology_relation r
    WHERE r.predicate = 'rdfs:subClassOf'
      AND EXISTS (SELECT 1 FROM envo_term WHERE id = r.subject)
      AND EXISTS (SELECT 1 FROM envo_term WHERE id = r.object)
    ON CONFLICT (id, ancestor_id) DO NOTHING
    """
    db.execute(text(insert_direct_parents_sql))

    # Indirect ancestors from closure
    insert_all_ancestors_sql = """
    INSERT INTO envo_ancestor (id, ancestor_id, direct)
    SELECT DISTINCT
        r.subject as id,
        r.object as ancestor_id,
        false as direct
    FROM ontology_relation r
    WHERE r.predicate = 'entailed_isa_partof_closure'
      AND EXISTS (SELECT 1 FROM envo_term WHERE id = r.subject)
      AND EXISTS (SELECT 1 FROM envo_term WHERE id = r.object)
    ON CONFLICT (id, ancestor_id) DO NOTHING
    """
    db.execute(text(insert_all_ancestors_sql))

    envo_term_count = db.execute(text("SELECT COUNT(*) FROM envo_term")).scalar()
    envo_ancestor_count = db.execute(text("SELECT COUNT(*) FROM envo_ancestor")).scalar()

    logger.info(
        f"Populated {envo_term_count} terms and {envo_ancestor_count} ancestor relationships"
    )


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


def _build_envo_subtree(db: Session, parent_id: str, visited_edges: Set[Tuple[str, str]]) -> None:
    # Track edges (child, parent) not just nodes - allows terms to have multiple parents
    query = (
        db.query(EnvoAncestor)
        .filter(EnvoAncestor.ancestor_id == parent_id)
        .filter(EnvoAncestor.direct.is_(True))
    )
    for node in query:
        edge = (node.id, parent_id)
        if edge in visited_edges:
            continue
        visited_edges.add(edge)

        statement = insert(EnvoTree.__table__).values({"id": node.id, "parent_id": parent_id})
        db.execute(statement)

        _build_envo_subtree(db, node.id, visited_edges)


def build_envo_trees(db: Session) -> None:
    """
    Convert the envo_ancestors graph into trees, and store them (normalized).

    If a node is encountered more than once, we arbitrarily choose its first
    encountered location in the graph.

    This should only be called after biosamples have been ingested.
    """
    db.execute(text(f"truncate table {EnvoTree.__tablename__}"))

    roots = get_biosample_roots(db)
    root_set = set(itertools.chain(*roots.values()))
    visited_edges: Set[Tuple[str, str]] = set()
    for root in root_set:
        statement = insert(EnvoTree.__table__).values(
            {
                "id": root,
                "parent_id": None,  # null parent_id indicates root node(s)
            }
        )
        db.execute(statement)

        _build_envo_subtree(db, root, visited_edges)

    db.commit()

    nested_envo_trees.cache_clear()


@dataclass
class _NodeInfo:
    id: str
    parent_id: str
    label: str


TreeChildren = Dict[Optional[str], List[_NodeInfo]]  # parent_id -> list of child nodes
TreeParents = Dict[str, List[_NodeInfo]]  # term_id -> list of nodes (one per parent relationship)


def _nested_envo_subtree(
    tree_children: TreeChildren,
    visited: Set[str],
    parent_id: Optional[str] = None,
) -> List[EnvoTreeNode]:
    return [
        EnvoTreeNode(
            id=node.id,
            label=node.label,
            children=_nested_envo_subtree(tree_children, visited, node.id),
        )
        for node in tree_children[parent_id]
        if node.id in visited
    ]


def _prune_useless_nodes(
    node: EnvoTreeNode,
    present_terms: Set[str],
    parent: Optional[EnvoTreeNode] = None,
    modified: bool = False,
) -> bool:
    """
    Remove useless internal (non-root) nodes from a tree.

    A useless node is one that is not in the terms present in the biosample set, and that has
    only a single child node.

    This modifies the structure in-place, returning the new root. Returns whether or not
    any modifications were made to the tree.
    """
    if parent is not None and len(node.children) == 1 and node.id not in present_terms:
        # Delete this node, move its only child up under the parent
        parent.children = [child for child in parent.children if child.id != node.id]
        node = node.children[0]
        parent.children.append(node)
        modified = True
        _prune_useless_nodes(node, present_terms, parent, modified)
    else:
        for child in node.children:
            modified |= _prune_useless_nodes(child, present_terms, node, modified)

    return modified


def _prune_useless_roots(node: EnvoTreeNode, present_terms: Set[str]) -> EnvoTreeNode:
    while len(node.children) == 1 and node.id not in present_terms:
        node = node.children[0]
    return node


def _get_trees_for_facet(
    db: Session,
    facet: str,
    tree_parents: TreeParents,
    tree_children: TreeChildren,
) -> List[EnvoTreeNode]:
    """Get the pruned trees for each facet."""
    query = db.query(getattr(Biosample, facet)).distinct()
    present_terms = set(r[0] for r in query) - {None}
    reachable: Set[str] = set()

    # Find all nodes reachable by walking up ALL parent chains (multi-parent aware)
    def mark_ancestors(term_id: str) -> None:
        if term_id in reachable:
            return
        reachable.add(term_id)
        for node in tree_parents.get(term_id, []):
            if node.parent_id is not None:
                mark_ancestors(node.parent_id)

    for term in present_terms:
        mark_ancestors(term)

    # Recursively build the tree structure
    root_nodes = _nested_envo_subtree(tree_children, reachable)

    # Prune useless internal nodes from the roots
    for root in root_nodes:
        # TODO I don't have a mathematical proof, but I think we might not need
        # this loop; because of the algorithm and tree structure, it might always get
        # pruned in a single pass. Not sure though.
        while _prune_useless_nodes(root, present_terms):
            pass

    return [_prune_useless_roots(root, present_terms) for root in root_nodes]


@functools.lru_cache(maxsize=None)
def nested_envo_trees() -> Dict[str, List[EnvoTreeNode]]:
    tree_children: TreeChildren = defaultdict(list)
    tree_parents: TreeParents = defaultdict(list)

    with SessionLocal() as session:
        query = session.query(EnvoTerm, EnvoTree).filter(EnvoTerm.id == EnvoTree.id)
        for term, edge in query:
            node = _NodeInfo(id=edge.id, parent_id=edge.parent_id, label=term.label)
            tree_children[edge.parent_id].append(node)
            tree_parents[edge.id].append(node)  # term can have multiple parent relationships

        return {
            facet: _get_trees_for_facet(session, facet, tree_parents, tree_children)
            for facet in ["env_broad_scale_id", "env_local_scale_id", "env_medium_id"]
        }
