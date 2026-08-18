# ==============================================================================
# NAMMAROUTE AI: BANGALORE TRANSIT FLASK API BACKEND PLATFORM
# Backed by CognoDB Cloud (openCypher over Bolt Protocol)
# ==============================================================================
import os
import sys
import logging
from contextlib import contextmanager
from flask import Flask, jsonify, request
from flask_cors import CORS
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, AuthError
from dotenv import load_dotenv

# Load local workspace configuration parameters
load_dotenv()

# Setup structured systems logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Initialize Core Flask Server with Cross-Origin Resource Sharing (CORS) handles
app = Flask(__name__)
CORS(app)  # Explicitly prevents cross-origin blocks from browser sessions (Port 5173 to 5000)

# ------------------------------------------------------------------------------
# COGNODB DATABASE LIFE-CYCLE MANAGEMENT POOL
# ------------------------------------------------------------------------------
class CognoDBConnectionManager:
    def __init__(self):
        self.uri = os.getenv("COGNODB_URI")
        self.username = os.getenv("COGNODB_USER", "cognodb")
        self.password = os.getenv("COGNODB_PASSWORD")
        self._driver: Driver = None

    def initialize_driver(self):
        if not self.uri or not self.password:
            logger.critical("Missing critical environment keys: COGNODB_URI or COGNODB_PASSWORD.")
            sys.exit("Error: Environment setup missing. See project configuration guides.")

        try:
            logger.info(f"Connecting to CognoDB instance pool over Bolt: {self.uri}")
            self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            self._driver.verify_connectivity()
            logger.info("Successfully established connection matrix with CognoDB Cloud cluster.")
        except AuthError:
            logger.error("Authentication handshake failure. Confirm 'cognodb' database user secrets.")
            raise
        except ServiceUnavailable as e:
            logger.error(f"Target CognoDB cluster is completely unreachable: {e}")
            raise

    def get_driver(self) -> Driver:
        if self._driver is None:
            self.initialize_driver()
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            logger.info("CognoDB connection registry pool cleared down.")

db_manager = CognoDBConnectionManager()

@contextmanager
def get_cognodb_session():
    """Transactional wrapper safeguarding clean tracking boundaries and resource reclamation."""
    try:
        driver = db_manager.get_driver()
        with driver.session() as session:
            yield session
    except ServiceUnavailable:
        logger.critical("Database lookup failed due to network connectivity failure.")
        raise

# ------------------------------------------------------------------------------
# API APPLICATION ENDPOINTS & CYPHER TRAVERSAL LAYER
# ------------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """System health check endpoint ensuring structural stability of backend connectivity."""
    try:
        db_manager.get_driver().verify_connectivity()
        return jsonify({"status": "active", "database": "connected"}), 200
    except Exception:
        return jsonify({"status": "degraded", "database": "unreachable"}), 503

@app.route("/api/transit/ripple-impact", methods=["GET"])
def multi_hop_delay_cascade():
    """
    REQUIREMENT 5.1: Multi-Hop Traversal (>= 2 hops)
    Traces outward impact down the network topology up to 3 hops deep.
    """
    target_station_id = request.args.get("station_id", "ST_MAJ")
    cypher_query = """
    MATCH path = (root:Station {id: $stationId})-[:CONNECTS_TO*1..3]-(downstream:Station)
    RETURN downstream.name AS AffectedStation,
           downstream.zone AS AffectedZone,
           length(path) AS DisruptionDistanceHops,
           [rel IN relationships(path) | rel.line] AS TransitLinesInvolved
    """
    try:
        with get_cognodb_session() as session:
            result = session.run(cypher_query, stationId=target_station_id)
            impact_matrix = [
                {
                    "station_name": record["AffectedStation"],
                    "zone": record["AffectedZone"],
                    "hops_away": record["DisruptionDistanceHops"],
                    "lines": record["TransitLinesInvolved"]
                }
                for record in result
            ]
            return jsonify({"status": "success", "impact_matrix": impact_matrix}), 200
    except ServiceUnavailable:
        return jsonify({"status": "error", "message": "Database unreachable."}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/transit/reroute", methods=["GET"])
def dynamic_reroute_avoiding_delays():
    """
    REQUIREMENT 5.1: High-complexity query an RDBMS would find highly awkward.
    Finds the absolute optimal pathing trajectory while filtering out disrupted segments.
    """
    origin = request.args.get("origin", "ST_JAY")
    destination = request.args.get("destination", "ST_ORR")

    # FIXED: Replaced openCypher's shortestPath() function with a variable-length path match (*1..10).
    # openCypher's shortestPath() optimization evaluates structural topology BEFORE applying
    # inline WHERE predicates. If the absolute shortest path is blocked, it throws an empty set
    # instead of evaluating the next best option. This approach guarantees fallback traversal.
    cypher_query = """
    MATCH (src:Station {id: $originId}), (dst:Station {id: $destinationId})
    MATCH path = (src)-[:CONNECTS_TO*1..10]-(dst)
        WHERE ALL(rel IN relationships(path) WHERE coalesce(rel.status, "Operational") <> "Delayed" AND coalesce(rel.status, "Operational") <> "Blocked")
            AND ALL(node IN nodes(path) WHERE node.id = $originId OR node.id = $destinationId OR coalesce(node.current_state, "Normal") <> "Alert")
    RETURN [node IN nodes(path) | node.name] AS RouteTrajectory,
           [rel IN relationships(path) | rel.mode] AS CommuteModes,
           REDUCE(total = 0, x IN relationships(path) | total + x.time_mins) AS TotalEstimatedTimeMins
    ORDER BY TotalEstimatedTimeMins ASC
    LIMIT 1
    """
    try:
        with get_cognodb_session() as session:
            result = session.run(cypher_query, originId=origin, destinationId=destination)
            record = result.single()
            
            if not record:
                return jsonify({"status": "no_path", "message": "No active functional routes match."}), 200

            return jsonify({
                "status": "success",
                "trajectory": record["RouteTrajectory"],
                "modes": record["CommuteModes"],
                "total_duration_minutes": record["TotalEstimatedTimeMins"]
            }), 200
    except ServiceUnavailable:
        return jsonify({"status": "error", "message": "Database layer cluster was unavailable."}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/transit/simulate-delay", methods=["POST"])
def simulate_system_delay():
    """
    DYNAMIC BOTTLENECK SIMULATION ENDPOINT
    Updates relationship properties dynamically across nodes to trigger immediate rerouting logic.
    """
    payload = request.json or {}
    source_id = payload.get("source_id", "ST_SILK")
    target_id = payload.get("target_id", "ST_ORR")
    new_status = payload.get("status", "Delayed")  # Can be 'Delayed' or 'Operational'

    cypher_query = """
    MATCH (src:Station {id: $srcId})-[r:CONNECTS_TO]-(dst:Station {id: $dstId})
    SET r.status = $status,
        src.current_state = CASE WHEN $status = "Operational" THEN "Normal" ELSE "Alert" END
    RETURN src.name AS SourceName, dst.name AS DestName, r.status AS CurrentStatus, src.current_state AS SourceState
    """
    try:
        with get_cognodb_session() as session:
            result = session.run(cypher_query, srcId=source_id, dstId=target_id, status=new_status)
            record = result.single()
            
            if record:
                logger.info(f"Transit link mutated: {record['SourceName']} -> {record['DestName']} is now {record['CurrentStatus']}.")
                return jsonify({
                    "status": "updated", 
                    "message": f"Path from {record['SourceName']} to {record['DestName']} marked as {record['CurrentStatus']}."
                }), 200
            
            return jsonify({"status": "not_found", "message": "Specified layout segment connection not found."}), 404
    except ServiceUnavailable:
        return jsonify({"status": "error", "message": "Database connectivity loss encountered during state rewrite."}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ------------------------------------------------------------------------------
# LOCAL INTEGRATION RUNNER ASSEMBLY ENTRY POINT
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Launch system server instance
    app.run(port=5000, debug=True)
