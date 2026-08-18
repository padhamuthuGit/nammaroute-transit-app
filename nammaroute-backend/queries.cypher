// ==============================================================================
// NAMMAROUTE AI: BANGALORE TRANSIT CORE CYPHER PRODUCTION QUERIES
// ==============================================================================

// 1. CLEAR DATABASE SCHEMA (Used in Data-Loading Initialization)
MATCH (n) 
DETACH DELETE n;

// 2. DATA INGESTION: STATION NODE CREATION (Parameterized)
CREATE (s:Station {
    id: $id, 
    name: $name, 
    type: $type, 
    zone: $zone,
    current_state: "Normal"
});

// 3. DATA INGESTION: RELATIONSHIP EDGE ROUTE CREATION (Parameterized)
MATCH (src:Station {id: $source})
MATCH (dst:Station {id: $target})
CREATE (src)-[r:CONNECTS_TO {
    mode: $mode,
    line: $line,
    time_mins: $time_mins,
    status: $status
}]->(dst);

// 4. REQUIREMENT 5.1: MULTI-HOP DELAY CASCADE TRAVERSAL
// Traces cascading transit impact up to 3 connections away outward from a central hub
MATCH path = (root:Station {id: $stationId})-[:CONNECTS_TO*1..3]-(downstream:Station)
RETURN downstream.name AS AffectedStation,
       downstream.zone AS AffectedZone,
       length(path) AS DisruptionDistanceHops,
       [rel IN relationships(path) | rel.line] AS TransitLinesInvolved;

// 5. REQUIREMENT 5.1: DYNAMIC ALTERNATIVE ROUTING (AWKWARD SQL EQUIVALENT)
// Evaluates variable-length network trajectories dynamically filtering out blocked links
MATCH (src:Station {id: $originId}), (dst:Station {id: $destinationId})
MATCH path = (src)-[:CONNECTS_TO*1..10]-(dst)
WHERE ALL(rel IN relationships(path) WHERE rel.status <> "Delayed" AND rel.status <> "Blocked")
RETURN [node IN nodes(path) | node.name] AS RouteTrajectory,
       [rel IN relationships(path) | rel.mode] AS CommuteModes,
       REDUCE(total = 0, x IN relationships(path) | total + x.time_mins) AS TotalEstimatedTimeMins
ORDER BY TotalEstimatedTimeMins ASC
LIMIT 1;

// 6. DYNAMIC LIVE SIMULATION GRIDLOCK UPDATE
MATCH (src:Station {id: $srcId})-[r:CONNECTS_TO]->(dst:Station {id: $dstId})
SET r.status = $status
RETURN src.name AS SourceName, dst.name AS DestName, r.status AS CurrentStatus;
