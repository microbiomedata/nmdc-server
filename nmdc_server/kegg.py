from nmdc_server.database import create_session
from nmdc_server.ingest.kegg import ingest_ko_pathway_map

with create_session() as session:
    ingest_ko_pathway_map(session)
