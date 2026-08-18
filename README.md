I've reformatted your README into a professional, GitHub-friendly structure with proper headings, sections, code blocks, lists, and diagrams.

NammaRoute AI Project Documentation
NammaRoute AI: Bangalore Transit Ripple-Effect & Dynamic Rerouting Engine

NammaRoute AI is a multi-modal transit analysis and dynamic pathfinding application tailored for Bangalore's dense urban commuting infrastructure, including the Namma Metro and BMTC high-frequency bus networks.

The application simulates real-time topological bottlenecks, such as:

Gridlock at Silk Board Junction
Signal failures at Majestic Interchange
Route disruptions and delays

Based on these events, the system dynamically calculates alternative transit routes using real-time edge filtering and graph traversal algorithms.

Project Links
Resource	LinkRepository	[Insert GitHub Repository URL]
Hosted Demo	[Insert Hosted Demo URL]
Screen Recording	[Insert Loom/Drive URL]
Submission	CognoDB Assignment 2 – Padhamuthu Mathialagan
1. Why a Graph Database?
Schema Justification

Public transportation networks are naturally interconnected systems consisting of stations, routes, transfers, and hubs. Representing these relationships efficiently is essential for real-time routing and disruption analysis.

Challenges with Relational Databases
Dynamic Multi-Hop Queries

Finding a route from Jayanagar to Outer Ring Road may involve:

Metro Green Line
      ↓
Metro Purple Line
      ↓
BMTC Feeder Bus


This requires an unpredictable number of JOIN operations, causing performance degradation as route complexity increases.

Dynamic Path Avoidance

If a critical node such as Silk Board Junction becomes unavailable, the system must instantly recalculate routes while excluding affected paths.

Implementing this behavior in SQL typically requires:

Recursive CTEs
Deeply nested joins
Complex maintenance
The CognoDB Advantage

CognoDB models the network directly as:

Nodes → Stations / Transit Hubs
Edges → Route Segments
Benefits
Index-Free Adjacency

Each station maintains direct references to connected stations rather than relying on costly global index scans.

O(1) Traversal

Graph traversal between adjacent stations operates in constant time.

Benefits include:

Faster shortest-path computation
Real-time route recalculation
Efficient multi-hop traversals
Scalability for large transportation networks
2. Graph Data Model

The application uses a Property Graph Model hosted on a free CognoDB Cloud c0 instance.

Graph Structure
[:CONNECTS_TO {mode:"METRO", line:"Purple"}]

(Station: Central) ─────────────► (Station: East)
       │                               ▲
       │                               │
       ▼                               │

(Station: South) ───────────────► (Station: South-East)

[:CONNECTS_TO {mode:"BUS", status:"Delayed"}]

Node Label: :Station
Property	Type	Descriptionid	String	Unique station identifier (e.g., ST_MAJ)
name	String	Station name
type	String	Metro_Station, Interchange_Hub, Bus_Terminal_Hub
zone	String	Central, South, East, etc.
current_state	String	Normal, Alert
Relationship Type: :CONNECTS_TO
Property	Type	Descriptionmode	String	METRO or BUS
line	String	Purple, Green, 500A_Exp, etc.
time_mins	Integer	Travel duration in minutes
status	String	Operational, Delayed, Blocked
3. Core Cypher Queries Explained

All database interactions are strictly parameterized through the official Neo4j driver to prevent Cypher injection vulnerabilities.

Query 1: Multi-Hop Delay Cascade
Objective

Determine the downstream impact of a disruption up to 3 hops away from an affected station.

Cypher Implementation
MATCH path =
(root:Station {id: $stationId})
-[:CONNECTS_TO*1..3]->
(downstream:Station)

RETURN
    downstream.name AS AffectedStation,
    downstream.zone AS AffectedZone,
    length(path) AS DisruptionDistanceHops,
    [rel IN relationships(path) | rel.line]
        AS TransitLinesInvolved

Explanation

This query:

Traverses up to three levels downstream
Identifies impacted stations
Determines disruption distance
Lists all transit lines involved

This enables transit engineers to understand ripple-effect impacts within the network.

Query 2: Dynamic Alternative Path Routing
Objective

Identify the shortest available route while avoiding delayed or blocked connections.

Cypher Implementation
MATCH
(src:Station {id: $originId}),
(dst:Station {id: $destinationId})

MATCH path =
shortestPath(
    (src)-[:CONNECTS_TO*..10]->(dst)
)

WHERE ALL(
    rel IN relationships(path)
    WHERE rel.status <> "Delayed"
      AND rel.status <> "Blocked"
)

RETURN
    [node IN nodes(path) | node.name]
        AS RouteTrajectory,

    [rel IN relationships(path) | rel.mode]
        AS CommuteModes,

    REDUCE(
        total = 0,
        x IN relationships(path)
        | total + x.time_mins
    ) AS TotalEstimatedTimeMins

Explanation

This query demonstrates the strength of graph databases by:

Running shortest-path calculations directly on the graph
Excluding disrupted routes in real time
Calculating travel duration on-the-fly

Traditional relational databases struggle to implement this cleanly and efficiently.

4. Engineering Architecture & Error Handling
System Architecture
┌─────────────────────────┐
│     React Frontend      │
│  (Vite + Tailwind CSS)  │
└───────────┬─────────────┘
            │ HTTP / JSON
            ▼
┌─────────────────────────┐
│    Flask Backend API    │
│       (Python 3)        │
└───────────┬─────────────┘
            │ Bolt Protocol
            ▼
┌─────────────────────────┐
│      CognoDB Cloud      │
│   Managed Graph DB      │
└─────────────────────────┘

Environment Separation

Sensitive configuration values are stored in:

.env


This file includes:

Database URI
User credentials
Authentication secrets

The file is excluded from source control using:

.gitignore

Graceful Degradation

The database access layer:

Uses context-managed sessions
Handles ServiceUnavailable exceptions
Handles authentication failures

If CognoDB becomes unavailable, the API returns:

503 Service Unavailable


The React frontend displays a user-friendly alert instead of crashing.

5. Local Setup & Running Instructions
Prerequisites
Python 3.10+
Node.js 18+
Database Setup
Create a free account at CognoDB.
Provision a c0 instance.
Copy:
Bolt URI
Username
Password
Backend Setup

Navigate to backend directory:

cd nammaroute-backend


Create environment file:

cp .env.example .env


Configure .env:

COGNODB_URI=bolt+s://<instance-id>.databases.cognodb.cloud
COGNODB_USER=cognodb
COGNODB_PASSWORD=<your-password>


Install dependencies:

pip install -r requirements.txt


Seed transit network data:

python seeder.py


Start backend server:

python app.py

Frontend Setup

Navigate to frontend directory:

cd nammaroute-frontend


Install dependencies:

npm install


Start development server:

npm run dev


Open:

http://localhost:5173

6. Application UI Layout Showcase
User Interface Design

The application uses a responsive two-column layout built with Tailwind CSS to support both desktop and mobile devices.

Left Panel: Simulation Dashboard

Provides controls to:

Introduce route disruptions
Trigger delay scenarios
Simulate network bottlenecks
Analyze transit behavior
Right Panel: Live Routing Timeline

Displays:

Real-time routing suggestions
Step-by-step travel instructions
Metro and Bus indicators
Loading and recalculation status
Delay warnings and route updates
Key Features

✅ Multi-modal route planning
 ✅ Dynamic disruption simulation
 ✅ Real-time shortest path calculation
 ✅ Delay-aware route recalculation
 ✅ Graph-native transit modeling
 ✅ Responsive React UI
 ✅ Flask-based API backend
 ✅ Cloud-hosted CognoDB database

This format is suitable for direct use as a professional GitHub README.md and significantly improves readability and evaluation score for project submissions.
