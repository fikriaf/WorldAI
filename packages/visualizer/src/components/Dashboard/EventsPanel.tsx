interface WorldEvent {
  tick: number
  type: string
  data: Record<string, unknown>
  timestamp: string
}

interface EventsPanelProps {
  events: WorldEvent[]
}

const EVENT_CONFIG: Record<string, { color: string; label: string; icon: JSX.Element }> = {
  abiogenesis: { 
    color: '#00ff88', 
    label: 'Abiogenesis',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 2a7 7 0 0 1 0 14" />
        <path d="M12 2a7 7 0 0 0 0 14" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    )
  },
  agent_born: { 
    color: '#00cc00', 
    label: 'Agent Born',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
        <line x1="12" y1="11" x2="12" y2="17" />
        <line x1="9" y1="14" x2="15" y2="14" />
      </svg>
    )
  },
  agent_died: { 
    color: '#ff4455', 
    label: 'Agent Died',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
        <line x1="9" y1="11" x2="15" y2="11" />
      </svg>
    )
  },
  agent_reproduced: { 
    color: '#00aaff', 
    label: 'Reproduced',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 8v8" />
        <path d="M8 12h8" />
      </svg>
    )
  },
  agent_stage_change: { 
    color: '#ffaa00', 
    label: 'Stage Change',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
        <polyline points="17 6 23 6 23 12" />
      </svg>
    )
  },
  chemical_reaction: { 
    color: '#ffff00', 
    label: 'Chemical Reaction',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M10 2v8L4 18a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2l-6-8V2" />
        <line x1="8" y1="2" x2="16" y2="2" />
        <path d="M7 13l3 3 7-7" />
      </svg>
    )
  },
  ca_pattern: { 
    color: '#ff00ff', 
    label: 'CA Pattern',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="3" y="3" width="7" height="7" />
        <rect x="14" y="3" width="7" height="7" />
        <rect x="14" y="14" width="7" height="7" />
        <rect x="3" y="14" width="7" height="7" />
      </svg>
    )
  },
}

const DefaultEventIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
)

const EmptyStateIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
)

function formatEventType(type: string): string {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function EventsPanel({ events }: EventsPanelProps) {
  const recentEvents = events.slice(-20).reverse()

  return (
    <div className="panel events-panel">
      <div className="panel-header">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
          Events
        </h3>
        <span className="panel-actions" style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
          {events.length > 0 ? `${events.length} total` : ''}
        </span>
      </div>
      <div 
        className="events-list" 
        role="log" 
        aria-label="World events log"
        aria-live="polite"
      >
        {recentEvents.length > 0 ? (
          recentEvents.map((event, index) => {
            const config = EVENT_CONFIG[event.type] || { 
              color: '#888', 
              label: formatEventType(event.type),
              icon: <DefaultEventIcon />
            }
            return (
              <div
                key={`${event.tick}-${index}`}
                className={`event-item ${event.type}`}
                style={{ borderLeftColor: config.color }}
                role="listitem"
                aria-label={`${config.label} at tick ${event.tick}`}
              >
                <span className="event-type" style={{ color: config.color }}>
                  <span className="event-type-icon" style={{ backgroundColor: config.color }} />
                  {config.icon}
                  <span>{config.label}</span>
                </span>
                <span className="event-tick" aria-label={`Tick ${event.tick}`}>
                  T:{event.tick.toLocaleString()}
                </span>
              </div>
            )
          })
        ) : (
          <div className="no-events" role="status">
            <EmptyStateIcon />
            <span>No events recorded yet</span>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              Events will appear as the simulation runs
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
