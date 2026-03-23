import { useEffect, useRef } from 'react'
import { useWorldStore } from '../../store/worldStore'

interface ChartProps {
  data: number[]
  label: string
  color: string
  maxValue?: number
}

function MiniChart({ data, label, color, maxValue }: ChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || data.length < 2) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    const width = canvas.width
    const height = canvas.height
    const max = maxValue || Math.max(...data, 0.001)
    const padding = 4
    
    ctx.clearRect(0, 0, width, height)
    
    ctx.strokeStyle = color
    ctx.lineWidth = 1.5
    ctx.beginPath()
    
    data.forEach((value, i) => {
      const x = (i / (data.length - 1)) * (width - padding * 2) + padding
      const y = height - (value / max) * (height - padding * 2) - padding
      
      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    
    ctx.stroke()
    
    const gradient = ctx.createLinearGradient(0, 0, 0, height)
    gradient.addColorStop(0, `${color}33`)
    gradient.addColorStop(1, `${color}00`)
    
    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.moveTo(padding, height - padding)
    
    data.forEach((value, i) => {
      const x = (i / (data.length - 1)) * (width - padding * 2) + padding
      const y = height - (value / max) * (height - padding * 2) - padding
      ctx.lineTo(x, y)
    })
    
    ctx.lineTo(width - padding, height - padding)
    ctx.closePath()
    ctx.fill()
  }, [data, color, maxValue])
  
  return (
    <div className="mini-chart">
      <div className="mini-chart-header">
        <span className="mini-chart-label">{label}</span>
        <span className="mini-chart-value" style={{ color }}>
          {data.length > 0 ? data[data.length - 1].toFixed(4) : '--'}
        </span>
      </div>
      <canvas 
        ref={canvasRef} 
        width={280} 
        height={60}
        className="chart-canvas"
      />
    </div>
  )
}

interface MetricsChartsProps {
  onClose?: () => void
}

export function MetricsCharts({ onClose }: MetricsChartsProps) {
  const { metrics, metrics_history, entropy_data, fetchMetrics, fetchMetricsHistory, fetchEntropy } = useWorldStore()
  
  useEffect(() => {
    fetchMetrics()
    fetchMetricsHistory(100)
    fetchEntropy()
    
    const interval = setInterval(() => {
      fetchMetrics()
      fetchEntropy()
    }, 2000)
    
    return () => clearInterval(interval)
  }, [fetchMetrics, fetchMetricsHistory, fetchEntropy])
  
  const entropyTrend = metrics_history.map(h => h.shannon_entropy)
  const complexityTrend = metrics_history.map(h => h.effective_complexity)
  const innovationTrend = metrics_history.map(h => h.innovation_rate)
  const phiTrend = metrics_history.map(h => h.avg_neural_phi)
  
  return (
    <div className="metrics-charts">
      <div className="metrics-charts-header">
        <h3>Metrics Analysis</h3>
        {onClose && (
          <button className="close-btn" onClick={onClose}>×</button>
        )}
      </div>
      
      {metrics && (
        <div className="metrics-current">
          <div className="metric-card">
            <span className="metric-card-label">Shannon Entropy</span>
            <span className="metric-card-value entropy">{metrics.shannon_entropy.toFixed(4)}</span>
          </div>
          <div className="metric-card">
            <span className="metric-card-label">Effective Complexity</span>
            <span className="metric-card-value complexity">{metrics.effective_complexity.toFixed(4)}</span>
          </div>
          <div className="metric-card">
            <span className="metric-card-label">Innovation Rate</span>
            <span className="metric-card-value innovation">{metrics.innovation_rate.toFixed(4)}</span>
          </div>
          <div className="metric-card">
            <span className="metric-card-label">Avg Neural Φ</span>
            <span className="metric-card-value phi">{metrics.avg_neural_phi.toFixed(4)}</span>
          </div>
          <div className="metric-card">
            <span className="metric-card-label">Genome Diversity</span>
            <span className="metric-card-value diversity">{metrics.genome_diversity.toFixed(4)}</span>
          </div>
          <div className="metric-card">
            <span className="metric-card-label">Species Count</span>
            <span className="metric-card-value species">{metrics.species_count}</span>
          </div>
        </div>
      )}
      
      <div className="charts-container">
        <MiniChart 
          data={entropyTrend} 
          label="Shannon Entropy" 
          color="var(--accent)" 
        />
        <MiniChart 
          data={complexityTrend} 
          label="Effective Complexity" 
          color="var(--accent-secondary)" 
        />
        <MiniChart 
          data={innovationTrend} 
          label="Innovation Rate" 
          color="var(--warning)" 
        />
        <MiniChart 
          data={phiTrend} 
          label="Avg Neural Phi" 
          color="#ff88ff" 
        />
      </div>
      
      {entropy_data && (
        <div className="entropy-details">
          <h4>Entropy Breakdown</h4>
          <div className="entropy-grid">
            <div className="entropy-item">
              <span className="entropy-label">Grid Entropy</span>
              <span className="entropy-value">{entropy_data.grid_entropy.toFixed(4)}</span>
            </div>
            <div className="entropy-item">
              <span className="entropy-label">Agent Entropy</span>
              <span className="entropy-value">{entropy_data.agent_entropy.toFixed(4)}</span>
            </div>
            <div className="entropy-item">
              <span className="entropy-label">Chemical Entropy</span>
              <span className="entropy-value">{entropy_data.chemical_entropy.toFixed(4)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}