import { useState, useEffect } from 'react'

interface TimelineEvent {
  tick: number
  type: string
  message: string
}

interface TimelineProps {
  currentTick: number
  maxTicks?: number
}

export function Timeline({ currentTick, maxTicks = 10000 }: TimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [zoom, setZoom] = useState(1)

  useEffect(() => {
    const stored = localStorage.getItem('world_timeline_events')
    if (stored) {
      try {
        setEvents(JSON.parse(stored))
      } catch (e) {
        console.error('Failed to parse timeline events', e)
      }
    }
  }, [])

  useEffect(() => {
    const newEvents: TimelineEvent[] = []
    if (currentTick > 0 && currentTick % 100 === 0) {
      newEvents.push({
        tick: currentTick,
        type: 'checkpoint',
        message: `Checkpoint at tick ${currentTick}`
      })
      const updated = [...events, ...newEvents].slice(-50)
      setEvents(updated)
      localStorage.setItem('world_timeline_events', JSON.stringify(updated))
    }
  }, [currentTick])

  const progress = Math.min((currentTick / maxTicks) * 100, 100)

  return (
    <div className="panel timeline-panel">
      <div className="timeline-header">
        <h3>Timeline</h3>
        <div className="timeline-controls">
          <button onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}>-</button>
          <span>{zoom.toFixed(1)}x</span>
          <button onClick={() => setZoom(z => Math.min(4, z + 0.25))}>+</button>
        </div>
      </div>
      
      <div className="timeline-track">
        <div 
          className="timeline-progress" 
          style={{ width: `${progress * zoom}%` }}
        />
        <div 
          className="timeline-marker"
          style={{ left: `${progress * zoom}%` }}
        />
      </div>
      
      <div className="timeline-labels">
        <span>0</span>
        <span>{Math.floor(maxTicks / 2)}</span>
        <span>{maxTicks}</span>
      </div>
      
      <div className="timeline-events">
        {events.slice(-10).map((event, i) => (
          <div key={i} className={`timeline-event ${event.type}`}>
            <span className="event-tick">T{event.tick}</span>
            <span className="event-message">{event.message}</span>
          </div>
        ))}
      </div>
    </div>
  )
}