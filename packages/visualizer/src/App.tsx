import { useState, useEffect } from 'react'
import { WorldRenderer } from './engine/WorldRenderer'
import { useWorldStore } from './store/worldStore'
import { StatsPanel } from './components/Dashboard/StatsPanel'
import { EventsPanel } from './components/Dashboard/EventsPanel'
import { ObserverPanel } from './components/Dashboard/ObserverPanel'
import { MetricsCharts } from './components/Dashboard/MetricsCharts'
import { ProfilingPanel } from './components/Dashboard/ProfilingPanel'
import { AgentInspector } from './components/Inspector/AgentInspector'
import { ControlBar } from './components/Controls/ControlBar'
import { GodModePanel } from './components/Controls/GodModePanel'
import './App.css'

function App() {
  const {
    tick,
    population,
    total_energy,
    agents,
    grid_data,
    running,
    selectedAgentId,
    heatmap_type,
    metrics,
    entropy_data,
    startWorld,
    stopWorld,
    step,
    run,
    fetchState,
    selectAgent,
    setHeatmapType,
  } = useWorldStore()

  const [showMetricsCharts, setShowMetricsCharts] = useState(false)
  const [showProfiling, setShowProfiling] = useState(false)

  const [config, setConfig] = useState({
    seed_id: 'genesis',
    grid_width: 64,
    grid_height: 64,
  })

  useEffect(() => {
    if (running) {
      const interval = setInterval(fetchState, 1000)
      return () => clearInterval(interval)
    }
  }, [running, fetchState])

  const handleStart = () => {
    startWorld(config)
  }

  const handleStop = () => {
    stopWorld()
  }

  const selectedAgent = agents.find((a) => a.id === selectedAgentId)

  return (
    <div className="app">
      <header className="header">
        <h1>World.ai</h1>
        <span className="subtitle">Genesis Engine v0.1.0</span>
      </header>

      <ControlBar
        running={running}
        onStart={handleStart}
        onStop={handleStop}
        onStep={step}
        onRun={() => run(100)}
        tick={tick}
        population={population}
        heatmapType={heatmap_type}
        onHeatmapChange={setHeatmapType}
        config={config}
        onConfigChange={setConfig}
      />

      <main className="main">
        <div className="canvas-container">
          <WorldRenderer 
            agents={agents} 
            gridData={grid_data}
            onAgentClick={selectAgent}
            heatmapType={heatmap_type}
          />
        </div>

        <aside className="sidebar">
          <StatsPanel
            tick={tick}
            population={population}
            totalEnergy={total_energy}
            metrics={metrics}
            entropy_data={entropy_data}
            onShowCharts={() => setShowMetricsCharts(true)}
            onShowProfiling={() => setShowProfiling(true)}
          />
          
          {selectedAgent && (
            <AgentInspector
              agent={selectedAgent}
              onClose={() => selectAgent(null)}
            />
          )}
          
          <EventsPanel events={useWorldStore.getState().recent_events} />
          
          <ObserverPanel />
          
          <GodModePanel />
        </aside>
      </main>

      {showMetricsCharts && (
        <div className="modal-overlay" onClick={() => setShowMetricsCharts(false)}>
          <div className="modal-content metrics-charts-modal" onClick={e => e.stopPropagation()}>
            <MetricsCharts onClose={() => setShowMetricsCharts(false)} />
          </div>
        </div>
      )}

      {showProfiling && (
        <div className="modal-overlay" onClick={() => setShowProfiling(false)}>
          <div className="modal-content profiling-modal" onClick={e => e.stopPropagation()}>
            <ProfilingPanel onClose={() => setShowProfiling(false)} />
          </div>
        </div>
      )}

      <footer className="footer">
        <span>Tick: {tick}</span>
        <span>Agents: {population}</span>
        <span>Energy: {total_energy.toFixed(2)}</span>
        {metrics && (
          <>
            <span>Entropy: {metrics.shannon_entropy.toFixed(3)}</span>
            <span>Complexity: {metrics.effective_complexity.toFixed(3)}</span>
          </>
        )}
      </footer>
    </div>
  )
}

export default App