import { useState, useEffect } from 'react'

interface MetricsData {
  tick: number
  shannon_entropy: number
  effective_complexity: number
  innovation_rate: number
  avg_neural_phi: number
  genome_diversity: number
  population: number
  species_count: number
}

interface MetricsPanelProps {
  tick: number
}

const API_BASE = 'http://localhost:8000'

export function MetricsPanel({ tick }: MetricsPanelProps) {
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [history, setHistory] = useState<number[]>([])

  useEffect(() => {
    fetch(`${API_BASE}/api/metrics`)
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(console.error)
  }, [tick])

  useEffect(() => {
    if (metrics) {
      setHistory(prev => [...prev.slice(-50), metrics.shannon_entropy])
    }
  }, [metrics?.shannon_entropy])

  if (!metrics) {
    return <div className="panel metrics-panel">Loading metrics...</div>
  }

  return (
    <div className="panel metrics-panel">
      <h3>Complexity Metrics</h3>
      
      <div className="metric-grid">
        <div className="metric">
          <span className="metric-label">Shannon Entropy</span>
          <span className="metric-value">{metrics.shannon_entropy.toFixed(3)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Effective Complexity</span>
          <span className="metric-value">{metrics.effective_complexity.toFixed(3)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Innovation Rate</span>
          <span className="metric-value">{metrics.innovation_rate.toFixed(4)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Avg Neural Φ</span>
          <span className="metric-value">{metrics.avg_neural_phi.toFixed(3)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Genome Diversity</span>
          <span className="metric-value">{metrics.genome_diversity.toFixed(3)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Species Count</span>
          <span className="metric-value">{metrics.species_count}</span>
        </div>
      </div>

      {history.length > 1 && (
        <div className="entropy-chart">
          <span className="chart-label">Entropy History</span>
          <div className="chart-bars">
            {history.map((val, i) => (
              <div 
                key={i} 
                className="bar" 
                style={{ height: `${Math.min(val * 100, 100)}%` }}
                title={`${val.toFixed(3)}`}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}