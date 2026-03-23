import { useMemo } from 'react'

interface WorkingMemoryItem {
  id: string
  content: string
  strength: number
  timestamp: number
}

interface EpisodicMemory {
  id: string
  event: string
  timestamp: number
  emotionalValence: number
}

interface SemanticNode {
  id: string
  label: string
  connections: string[]
}

interface MemoryVizProps {
  workingMemory?: WorkingMemoryItem[]
  episodicMemory?: EpisodicMemory[]
  semanticMemory?: SemanticNode[]
  onNodeClick?: (nodeId: string) => void
}

export function MemoryViz({
  workingMemory = [],
  episodicMemory = [],
  semanticMemory = [],
  onNodeClick,
}: MemoryVizProps) {
  const sortedEpisodic = useMemo(() => {
    return [...episodicMemory].sort((a, b) => b.timestamp - a.timestamp).slice(0, 10)
  }, [episodicMemory])

  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {}
    const count = semanticMemory.length
    const centerX = 150
    const centerY = 120
    const radius = 80
    
    semanticMemory.forEach((node, i) => {
      const angle = (i / count) * 2 * Math.PI - Math.PI / 2
      positions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      }
    })
    return positions
  }, [semanticMemory])

  return (
    <div className="memory-viz">
      <div className="memory-section">
        <h4>Working Memory</h4>
        <div className="working-memory-list">
          {workingMemory.length === 0 ? (
            <div className="empty-state">No working memory</div>
          ) : (
            workingMemory.map((item) => (
              <div key={item.id} className="memory-item">
                <div className="memory-content">{item.content}</div>
                <div className="memory-strength">
                  <div
                    className="strength-bar"
                    style={{ width: `${item.strength * 100}%` }}
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="memory-section">
        <h4>Episodic Memory</h4>
        <div className="episodic-timeline">
          {sortedEpisodic.length === 0 ? (
            <div className="empty-state">No episodic memories</div>
          ) : (
            sortedEpisodic.map((mem) => (
              <div
                key={mem.id}
                className="episodic-item"
                style={{
                  borderLeftColor: mem.emotionalValence > 0 ? '#00ff88' : '#ff4444',
                }}
              >
                <div className="episodic-event">{mem.event}</div>
                <div className="episodic-time">
                  {new Date(mem.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="memory-section">
        <h4>Semantic Memory</h4>
        <svg className="semantic-graph" width="300" height="240">
          {semanticMemory.map((node) => {
            const pos = nodePositions[node.id]
            if (!pos) return null
            return (
              <g key={node.id}>
                {node.connections.map((targetId) => {
                  const targetPos = nodePositions[targetId]
                  if (!targetPos) return null
                  return (
                    <line
                      key={`${node.id}-${targetId}`}
                      x1={pos.x}
                      y1={pos.y}
                      x2={targetPos.x}
                      y2={targetPos.y}
                      stroke="#445566"
                      strokeWidth="1.5"
                      opacity="0.6"
                    />
                  )
                })}
              </g>
            )
          })}
          {semanticMemory.map((node) => {
            const pos = nodePositions[node.id]
            if (!pos) return null
            return (
              <g
                key={node.id}
                onClick={() => onNodeClick?.(node.id)}
                style={{ cursor: 'pointer' }}
              >
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="20"
                  fill="#2a3a4a"
                  stroke="#00ff88"
                  strokeWidth="2"
                />
                <text
                  x={pos.x}
                  y={pos.y + 4}
                  textAnchor="middle"
                  fill="#ffffff"
                  fontSize="9"
                >
                  {node.label}
                </text>
              </g>
            )
          })}
        </svg>
        {semanticMemory.length === 0 && (
          <div className="empty-state">No semantic nodes</div>
        )}
      </div>
    </div>
  )
}