import { useMemo } from 'react'

interface StatsPanelProps {
  tick: number
  population: number
  totalEnergy: number
  metrics?: {
    shannon_entropy: number
    effective_complexity: number
    innovation_rate: number
    avg_neural_phi: number
    genome_diversity: number
    species_count: number
  } | null
  entropy_data?: {
    shannon_entropy: number
    grid_entropy: number
    agent_entropy: number
    chemical_entropy: number
  } | null
  onShowCharts?: () => void
  onShowProfiling?: () => void
}

const TickIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
)

const PopulationIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </svg>
)

const EnergyIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
)

const SpeciesIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 2L2 7l10 5 10-5-10-5z" />
    <path d="M2 17l10 5 10-5" />
    <path d="M2 12l10 5 10-5" />
  </svg>
)

const ChartIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </svg>
)

const ProfilingIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 8 14" />
  </svg>
)

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toLocaleString()
}

export function StatsPanel({ 
  tick, 
  population, 
  totalEnergy, 
  metrics, 
  entropy_data, 
  onShowCharts, 
  onShowProfiling 
}: StatsPanelProps) {
  const stats = useMemo(() => [
    {
      label: 'Tick',
      value: formatNumber(tick),
      icon: TickIcon,
      className: '',
    },
    {
      label: 'Population',
      value: formatNumber(population),
      icon: PopulationIcon,
      className: '',
    },
    {
      label: 'Total Energy',
      value: totalEnergy.toFixed(2),
      icon: EnergyIcon,
      className: '',
    },
    {
      label: 'Species',
      value: metrics?.species_count?.toLocaleString() ?? '--',
      icon: SpeciesIcon,
      className: '',
    },
  ], [tick, population, totalEnergy, metrics?.species_count])

  return (
    <div className="panel stats-panel">
      <div className="panel-header">
        <h3>
          <ChartIcon />
          World Stats
        </h3>
      </div>
      <div className="stat-grid" role="region" aria-label="World statistics">
        {stats.map((stat) => (
          <div 
            key={stat.label} 
            className="stat-card" 
            role="region" 
            aria-label={`${stat.label}: ${stat.value}`}
          >
            <div className="stat-card-header">
              <div className="stat-icon" aria-hidden="true">
                <stat.icon />
              </div>
              <span className="stat-card-label">{stat.label}</span>
            </div>
            <span className="stat-card-value">{stat.value}</span>
          </div>
        ))}
      </div>
      
      {metrics && (
        <div className="metrics-mini" role="region" aria-label="Complexity metrics summary">
          <div className="metrics-mini-header">
            <h4>Complexity Metrics</h4>
            {onShowCharts && (
              <button 
                className="view-more-btn" 
                onClick={onShowCharts}
                aria-label="View detailed charts"
              >
                Charts
              </button>
            )}
          </div>
          <div className="metrics-mini-grid">
            <div className="metric-mini">
              <span className="metric-mini-label">Entropy</span>
              <span className="metric-mini-value entropy" aria-label={`Shannon entropy: ${metrics.shannon_entropy.toFixed(3)}`}>
                {metrics.shannon_entropy.toFixed(3)}
              </span>
            </div>
            <div className="metric-mini">
              <span className="metric-mini-label">Complexity</span>
              <span className="metric-mini-value complexity" aria-label={`Effective complexity: ${metrics.effective_complexity.toFixed(3)}`}>
                {metrics.effective_complexity.toFixed(3)}
              </span>
            </div>
            <div className="metric-mini">
              <span className="metric-mini-label">Innovation</span>
              <span className="metric-mini-value innovation" aria-label={`Innovation rate: ${metrics.innovation_rate.toFixed(4)}`}>
                {metrics.innovation_rate.toFixed(4)}
              </span>
            </div>
            <div className="metric-mini">
              <span className="metric-mini-label">Neural Φ</span>
              <span className="metric-mini-value phi" aria-label={`Average neural phi: ${metrics.avg_neural_phi.toFixed(3)}`}>
                {metrics.avg_neural_phi.toFixed(3)}
              </span>
            </div>
          </div>
        </div>
      )}
      
      {entropy_data && (
        <div className="entropy-mini" role="region" aria-label="Entropy breakdown">
          <h4>Entropy Breakdown</h4>
          <div className="entropy-mini-grid">
            <div className="entropy-mini-item">
              <span className="entropy-mini-label">Grid</span>
              <span className="entropy-mini-value" aria-label={`Grid entropy: ${entropy_data.grid_entropy.toFixed(3)}`}>
                {entropy_data.grid_entropy.toFixed(3)}
              </span>
            </div>
            <div className="entropy-mini-item">
              <span className="entropy-mini-label">Agent</span>
              <span className="entropy-mini-value" aria-label={`Agent entropy: ${entropy_data.agent_entropy.toFixed(3)}`}>
                {entropy_data.agent_entropy.toFixed(3)}
              </span>
            </div>
            <div className="entropy-mini-item">
              <span className="entropy-mini-label">Chemical</span>
              <span className="entropy-mini-value" aria-label={`Chemical entropy: ${entropy_data.chemical_entropy.toFixed(3)}`}>
                {entropy_data.chemical_entropy.toFixed(3)}
              </span>
            </div>
          </div>
        </div>
      )}
      
      {onShowProfiling && (
        <div className="profiling-link">
          <button 
            className="profiling-btn" 
            onClick={onShowProfiling}
            aria-label="View profiling statistics"
          >
            <ProfilingIcon />
            View Profiling Stats
          </button>
        </div>
      )}
    </div>
  )
}
