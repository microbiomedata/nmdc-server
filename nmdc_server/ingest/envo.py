import json
from collections import defaultdict
from typing import Dict, Set
from urllib import request

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from nmdc_server import models

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

        statement = insert(models.EnvoAncestor.__table__).values(
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
            sql = insert(models.EnvoTerm.__table__).values(envo_data)
            db.execute(sql.on_conflict_do_update(constraint="pk_envo_term", set_=envo_data))
            ids.add(id)

        db.flush()

        for node in ids:
            ancestor_data = dict(id=node, ancestor_id=node, direct=False)
            sql = insert(models.EnvoAncestor.__table__).values(ancestor_data)
            db.execute(sql.on_conflict_do_nothing())
            db.flush()
            populate_envo_ancestor(db, node, node, direct_ancestors, ids, True, set())

    db.commit()
