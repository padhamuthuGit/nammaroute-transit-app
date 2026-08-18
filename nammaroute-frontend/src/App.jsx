import { useEffect, useState } from 'react';
import { AlertTriangle, ArrowRight, Bus, CheckCircle, MapPin, RefreshCw, Train } from 'lucide-react';

const BACKEND_URL = 'https://nammaroute-backend-da06.onrender.com';

const STATIONS = [
  { id: 'ST_MAJ', name: 'Majestic (Kempegowda Hub)', type: 'Interchange_Hub' },
  { id: 'ST_MG', name: 'MG Road Metro', type: 'Metro_Station' },
  { id: 'ST_IND', name: 'Indiranagar Metro', type: 'Metro_Station' },
  { id: 'ST_BYP', name: 'Baiyappanahalli Metro', type: 'Metro_Station' },
  { id: 'ST_JAY', name: 'Jayanagar Metro', type: 'Metro_Station' },
  { id: 'ST_JP', name: 'JP Nagar Metro', type: 'Metro_Station' },
  { id: 'ST_SILK', name: 'Silk Board Junction', type: 'Bus_Terminal_Hub' },
  { id: 'ST_ORR', name: 'Outer Ring Road (EcoSpace)', type: 'Bus_Stop' },
];

export default function App() {
  const [origin, setOrigin] = useState('ST_JAY');
  const [destination, setDestination] = useState('ST_ORR');
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [systemHealthy, setSystemHealthy] = useState(null);
  const [isJamSimulated, setIsJamSimulated] = useState(false);
  const [simulationLoading, setSimulationLoading] = useState(false);

  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/health`);
      const data = await res.json();
      setSystemHealthy(data.status === 'active');
    } catch {
      setSystemHealthy(false);
    }
  };

  const handleFindRoute = async () => {
    setLoading(true);
    setError(null);
    setRoute(null);

    try {
      const res = await fetch(`${BACKEND_URL}/api/transit/reroute?origin=${origin}&destination=${destination}`);
      const data = await res.json();

      if (data.status === 'success') {
        setRoute(data);
      } else if (data.status === 'no_path') {
        setError('All transport routes between these stations are currently blocked.');
      } else {
        setError(data.message || 'Could not calculate a route at this time.');
      }
    } catch {
      setError('The route planner cannot connect to the network right now.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleJam = async () => {
    setSimulationLoading(true);
    const nextJamState = !isJamSimulated;

    try {
      const res = await fetch(`${BACKEND_URL}/api/transit/simulate-delay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: 'ST_SILK',
          target_id: 'ST_ORR',
          status: nextJamState ? 'Delayed' : 'Operational',
        }),
      });
      const data = await res.json();

      if (res.status === 200) {
        setIsJamSimulated(nextJamState);
        if (route || error) {
          handleFindRoute();
        }
      } else {
        alert(`Simulation Error: ${data.message}`);
      }
    } catch {
      alert('Failed to trigger the traffic jam simulation.');
    } finally {
      setSimulationLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand-group">
          <div className="brand-mark">NMAI</div>
          <div>
            <h1 className="brand-title">NammaRoute AI</h1>
            <p className="brand-subtitle">Bangalore Smart Commute Planner</p>
          </div>
        </div>

        <div>
          {systemHealthy === true && (
            <span className="status-badge status-online">
              <CheckCircle className="icon-sm icon-online" /> Live System Active
            </span>
          )}
          {systemHealthy === false && (
            <span className="status-badge status-offline">
              <AlertTriangle className="icon-sm icon-offline" /> Network Offline
            </span>
          )}
          {systemHealthy === null && (
            <span className="status-badge status-checking">
              <RefreshCw className="icon-sm spin" /> Connecting...
            </span>
          )}
        </div>
      </header>

      <main className="dashboard-grid">
        <section className="left-column">
          <div className="panel-card">
            <h2 className="section-title">
              <MapPin className="icon-md icon-primary" /> Plan Your Trip
            </h2>

            <div className="field-stack">
              <div>
                <label className="field-label">Starting From</label>
                <select value={origin} onChange={(event) => setOrigin(event.target.value)} className="field-select">
                  {STATIONS.map((station) => <option key={station.id} value={station.id}>{station.name}</option>)}
                </select>
              </div>

              <div>
                <label className="field-label">Going To</label>
                <select value={destination} onChange={(event) => setDestination(event.target.value)} className="field-select">
                  {STATIONS.map((station) => <option key={station.id} value={station.id}>{station.name}</option>)}
                </select>
              </div>

              <button onClick={handleFindRoute} disabled={loading || systemHealthy === false} className="primary-button">
                {loading ? <RefreshCw className="icon-md spin" /> : <span>Search Best Route</span>}
              </button>
            </div>
          </div>

          <div className="panel-card">
            <h2 className="section-title">
              <AlertTriangle className="icon-md icon-warning" /> Test Traffic Conditions
            </h2>
            <p className="helper-text">
              Use this switch to trigger a live traffic block on the Silk Board highway corridor to see how the system immediately re-plans your trip.
            </p>

            <div className="simulator-row">
              <div>
                <span className="simulator-title">Silk Board Gridlock</span>
                <span className="simulator-copy">Block the direct outer ring road route</span>
              </div>

              <button onClick={handleToggleJam} disabled={simulationLoading} className={`switch ${isJamSimulated ? 'switch-on' : ''}`}>
                <span className="switch-knob" />
              </button>
            </div>
          </div>
        </section>

        <section className="right-column">
          <div className="result-card">
            <div className="result-main">
              <h2 className="result-title">Your Suggested Travel Plan</h2>

              {!route && !loading && !error && (
                <div className="empty-state">
                  <p>Choose your start and end points on the left to see your journey steps.</p>
                </div>
              )}

              {loading && (
                <div className="loading-state">
                  <RefreshCw className="loading-icon spin" />
                  <p>Calculating open routes...</p>
                </div>
              )}

              {error && (
                <div className="error-card">
                  <AlertTriangle className="error-icon" />
                  <div>
                    <span className="error-title">Travel Delay Notice</span>
                    <p>{error}</p>
                  </div>
                </div>
              )}

              {route && (
                <div className="route-content">
                  <div className="duration-row">
                    <div>
                      Estimated Duration: <span>{route.total_duration_minutes} mins</span>
                    </div>
                    {isJamSimulated && <span className="detour-badge">Traffic Detour Active</span>}
                  </div>

                  <div className="timeline">
                    {route.trajectory.map((stationName, index) => {
                      const isLast = index === route.trajectory.length - 1;
                      const transportMode = !isLast ? route.modes[index] : null;

                      return (
                        <div key={stationName} className="timeline-item">
                          <div className={`timeline-dot ${isLast ? 'timeline-dot-final' : ''}`} />
                          <div className="timeline-body">
                            <span className={`station-name ${isLast ? 'station-name-final' : ''}`}>{stationName}</span>

                            {!isLast && transportMode && (
                              <div className="mode-chip">
                                {transportMode === 'METRO' ? <Train className="icon-xs icon-train" /> : <Bus className="icon-xs icon-bus" />}
                                <span>{transportMode === 'METRO' ? 'Take Metro Train' : 'Take BMTC Bus'}</span>
                                <ArrowRight className="icon-arrow" />
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {route && isJamSimulated && (
              <div className="route-note">
                Note: The app automatically diverted you through the Majestic Metro station loop to avoid the heavy traffic jam currently simulated at Silk Board Junction.
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
