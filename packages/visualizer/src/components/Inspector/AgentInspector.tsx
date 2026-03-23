interface Agent {
  id: string
  position_x: number
  position_y: number
  energy: number
  health: number
  age_ticks: number
  stage: string
  genome_hash: string
}

interface AgentInspectorProps {
  agent: Agent
  onClose: () => void
}

const CloseIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
)

const AgentIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
)

const StageIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
    <polyline points="17 6 23 6 23 12" />
  </svg>
)

const PositionIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <line x1="12" y1="2" x2="12" y2="22" />
  </svg>
)

const EnergyIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
)

const HealthIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
  </svg>
)

const AgeIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
)

const GenomeIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M19.07 4.93L4.93 19.07" />
    <circle cx="12" cy="12" r="4" />
  </svg>
)

const HashIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="4" y1="9" x2="20" y2="9" />
    <line x1="4" y1="15" x2="20" y2="15" />
    <line x1="10" y1="3" x2="8" y2="21" />
    <line x1="16" y1="3" x2="14" y2="21" />
  </svg>
)

function getStageColor(stage: string): string {
  const stageColors: Record<string, string> = {
    embryo: '#00ff88',
    juvenile: '#00cc00',
    adult: '#00aaff',
    mature: '#ffaa00',
    elder: '#ff4444',
  }
  return stageColors[stage.toLowerCase()] || '#888888'
}

function getEnergyLevel(energy: number): { label: string; color: string } {
  if (energy > 0.7) return { label: 'High', color: 'var(--accent)' }
  if (energy > 0.3) return { label: 'Medium', color: 'var(--warning)' }
  return { label: 'Low', color: 'var(--danger)' }
}

function getHealthLevel(health: number): { label: string; color: string } {
  if (health > 0.7) return { label: 'Healthy', color: 'var(--accent)' }
  if (health > 0.3) return { label: 'Weakened', color: 'var(--warning)' }
  return { label: 'Critical', color: 'var(--danger)' }
}

export function AgentInspector({ agent, onClose }: AgentInspectorProps) {
  const energyLevel = getEnergyLevel(agent.energy)
  const healthLevel = getHealthLevel(agent.health)
  const stageColor = getStageColor(agent.stage)

  return (
    <div className="agent-inspector" role="region" aria-label="Agent Inspector">
      <div className="inspector-header">
        <h3>
          <AgentIcon />
          Agent Inspector
        </h3>
        <button 
          className="close-btn" 
          onClick={onClose}
          aria-label="Close agent inspector"
        >
          <CloseIcon />
        </button>
      </div>
      <div className="inspector-content">
        <div className="inspector-field">
          <span className="field-label">
            <HashIcon /> ID
          </span>
          <span className="field-value" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
            {agent.id}
          </span>
        </div>
        
        <div className="inspector-field">
          <span className="field-label">
            <StageIcon /> Stage
          </span>
          <span 
            className="stage-badge" 
            style={{ 
              borderColor: stageColor,
              color: stageColor,
              background: `${stageColor}15`
            }}
          >
            {agent.stage}
          </span>
        </div>
        
        <div className="inspector-field">
          <span className="field-label">
            <PositionIcon /> Position
          </span>
          <span className="field-value">
            ({agent.position_x.toFixed(2)}, {agent.position_y.toFixed(2)})
          </span>
        </div>
        
        <div className="inspector-field">
          <span className="field-label">
            <EnergyIcon /> Energy
          </span>
          <div className="progress-bar-with-value">
            <div className="progress-bar" role="progressbar" aria-valuenow={agent.energy * 100} aria-valuemin={0} aria-valuemax={100}>
              <div 
                className="progress-fill energy" 
                style={{ width: `${agent.energy * 100}%` }}
              />
            </div>
            <span className="progress-value" style={{ color: energyLevel.color }}>
              {agent.energy.toFixed(2)} ({energyLevel.label})
            </span>
          </div>
        </div>
        
        <div className="inspector-field">
          <span className="field-label">
            <HealthIcon /> Health
          </span>
          <div className="progress-bar-with-value">
            <div className="progress-bar" role="progressbar" aria-valuenow={agent.health * 100} aria-valuemin={0} aria-valuemax={100}>
              <div 
                className="progress-fill health" 
                style={{ width: `${agent.health * 100}%` }}
              />
            </div>
            <span className="progress-value" style={{ color: healthLevel.color }}>
              {agent.health.toFixed(2)} ({healthLevel.label})
            </span>
          </div>
        </div>
        
        <div className="inspector-field">
          <span className="field-label">
            <AgeIcon /> Age
          </span>
          <span className="field-value">
            {agent.age_ticks.toLocaleString()} ticks
          </span>
        </div>
        
        <div className="inspector-field">
          <span className="field-label">
            <GenomeIcon /> Genome
          </span>
          <span className="field-value hash" title={agent.genome_hash}>
            <HashIcon style={{ width: '12px', height: '12px', marginRight: '4px', opacity: 0.5 }} />
            {agent.genome_hash.length > 32 
              ? `${agent.genome_hash.slice(0, 32)}...` 
              : agent.genome_hash}
          </span>
        </div>
      </div>
    </div>
  )
}
