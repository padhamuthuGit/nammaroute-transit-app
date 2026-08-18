import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# BANGALORE METRO & BUS NETWORK DATASET
# ------------------------------------------------------------------------------
STATIONS = [
    {"id": "ST_MAJ", "name": "Majestic (Kempegowda)", "type": "Interchange_Hub", "zone": "Central"},
    {"id": "ST_MG", "name": "MG Road", "type": "Metro_Station", "zone": "Central"},
    {"id": "ST_IND", "name": "Indiranagar", "type": "Metro_Station", "zone": "East"},
    {"id": "ST_BYP", "name": "Baiyappanahalli", "type": "Metro_Station", "zone": "East"},
    {"id": "ST_JAY", "name": "Jayanagar", "type": "Metro_Station", "zone": "South"},
    {"id": "ST_JP", "name": "JP Nagar", "type": "Metro_Station", "zone": "South"},
    {"id": "ST_SILK", "name": "Silk Board Junction", "type": "Bus_Terminal_Hub", "zone": "South-East"},
    {"id": "ST_ORR", "name": "Outer Ring Road (EcoSpace)", "type": "Bus_Stop", "zone": "East-Belt"}
]

CONNECTIONS = [
    # Namma Metro Purple Line (Directional links)
    {"source": "ST_MAJ", "target": "ST_MG", "mode": "METRO", "line": "Purple", "time_mins": 7, "status": "Operational"},
    {"source": "ST_MG", "target": "ST_IND", "mode": "METRO", "line": "Purple", "time_mins": 8, "status": "Operational"},
    {"source": "ST_IND", "target": "ST_BYP", "mode": "METRO", "line": "Purple", "time_mins": 5, "status": "Operational"},
    
    # Namma Metro Green Line
    {"source": "ST_MAJ", "target": "ST_JAY", "mode": "METRO", "line": "Green", "time_mins": 12, "status": "Operational"},
    {"source": "ST_JAY", "target": "ST_JP", "mode": "METRO", "line": "Green", "time_mins": 4, "status": "Operational"},
    
    # BMTC High-Frequency Feeder Routes (Simplifying major high-traffic bottlenecks)
    {"source": "ST_JP", "target": "ST_SILK", "mode": "BUS", "line": "500B", "time_mins": 25, "status": "Operational"},
    {"source": "ST_JAY", "target": "ST_SILK", "mode": "BUS", "line": "215Z", "time_mins": 30, "status": "Operational"},
    {"source": "ST_SILK", "target": "ST_ORR", "mode": "BUS", "line": "500A_Exp", "time_mins": 15, "status": "Operational"},
    {"source": "ST_BYP", "target": "ST_ORR", "mode": "BUS", "line": "MF-12", "time_mins": 22, "status": "Operational"}
]

def run_seeder():
    uri = os.getenv("COGNODB_URI")
    user = os.getenv("COGNODB_USER", "cognodb")
    password = os.getenv("COGNODB_PASSWORD")

    if not uri or not password:
        logger.error("Seeding failed: Missing COGNODB_URI or COGNODB_PASSWORD in .env file.")
        return

    logger.info("Connecting to CognoDB instance...")
    try:
        # CognoDB uses official neo4j drivers over Bolt secure protocol
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # 1. Clear any old data to prevent duplication (Mandatory for clean retries)
            logger.info("Purging old graph entries...")
            session.run("MATCH (n) DETACH DELETE n")

            # 2. Insert Nodes securely using Parameterized Queries (Requirement 5.1)
            logger.info(f"Injecting {len(STATIONS)} station nodes...")
            node_cypher = """
            CREATE (s:Station {
                id: $id, 
                name: $name, 
                type: $type, 
                zone: $zone,
                current_state: "Normal"
            })
            """
            for station in STATIONS:
                session.run(node_cypher, **station)

            # 3. Insert Relationships connecting the mesh topology
            logger.info(f"Building {len(CONNECTIONS)} route edges...")
            edge_cypher = """
            MATCH (src:Station {id: $source})
            MATCH (dst:Station {id: $target})
            CREATE (src)-[r:CONNECTS_TO {
                mode: $mode,
                line: $line,
                time_mins: $time_mins,
                status: $status
            }]->(dst)
            """
            for connection in CONNECTIONS:
                session.run(edge_cypher, **connection)

        driver.close()
        logger.info("🎉 Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"An error occurred during database seeding: {e}")

if __name__ == "__main__":
    run_seeder()
