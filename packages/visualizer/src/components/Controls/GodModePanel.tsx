import { useState, useEffect } from 'react'
import { useWorldStore } from '../../store/worldStore'

type InterventionType = 'boost_energy' | 'kill' | 'teleport' | 'modify_genome' | 'spawn'

const INTERVENTION_TYPES: { value: InterventionType; label: string; danger: boolean }[] = [
  { value: 'boost_energy', label: 'Boost Energy', danger: false },
  { value: 'kill', label: 'Kill Agent', danger: true },
  { value: 'teleport', label: 'Teleport', danger: false },
  { value: 'modify_genome', label: 'Modify Genome', danger: false },
  { value: 'spawn', label: 'Spawn Agent', danger: false },
]

export function GodModePanel() {
  const {
    god_mode_enabled,
    god_mode_audit_log,
    intervention_count,
    fetchGodModeState,
    enableGodMode,
    disableGodMode,
    performIntervention,
    clearAuditLog,
    agents,
    running,
  } = useWorldStore()

  const [targetId, setTargetId] = useState('')
  const [interventionType, setInterventionType] = useState<InterventionType>('boost_energy')
  const [parameters, setParameters] = useState<Record<string, string>>({})
  const [executing, setExecuting] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    fetchGodModeState()
  }, [fetchGodModeState])

  const handleToggle = async () => {
    if (god_mode_enabled) {
      await disableGodMode()
    } else {
      await enableGodMode()
    }
  }

  const handleExecute = async () => {
    if (!targetId.trim()) {
      setMessage({ type: 'error', text: 'Target ID is required' })
      return
    }

    setExecuting(true)
    setMessage(null)

    const params: Record<string, unknown> = {}
    if (interventionType === 'teleport') {
      params.x = parseFloat(parameters.x) || 0
      params.y = parseFloat(parameters.y) || 0
    }

    const result = await performIntervention(targetId, interventionType, params)
    
    if (result.status === 'success') {
      setMessage({ type: 'success', text: `Intervention "${interventionType}" executed successfully` })
      setTargetId('')
      setParameters({})
    } else {
      setMessage({ type: 'error', text: `Intervention failed: ${result.status}` })
    }
    
    setExecuting(false)
  }

  const handleClearAudit = async () => {
    await clearAuditLog()
    setMessage({ type: 'success', text: 'Audit log cleared' })
  }

  const selectedIntervention = INTERVENTION_TYPES.find(i => i.value === interventionType)

  return (
    <div className="godmode-panel">
      <div className="godmode-header">
        <h3>God Mode</h3>
        <span className="intervention-count">{intervention_count} interventions</span>
      </div>

      <div className="godmode-toggle">
        <label className="toggle-label">
          <span>Enable God Mode</span>
          <input
            type="checkbox"
            checked={god_mode_enabled}
            onChange={handleToggle}
            disabled={!running}
          />
          <span className={`toggle-state ${god_mode_enabled ? 'active' : ''}`}>
            {god_mode_enabled ? 'ACTIVE' : 'OFF'}
          </span>
        </label>
        {!running && <span className="warning-text">Start world to enable</span>}
      </div>

      {god_mode_enabled && (
        <div className="godmode-controls">
          <div className="control-section">
            <h4>Intervention</h4>
            
            <div className="form-group">
              <label>Target Agent ID</label>
              <select
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                disabled={!running}
              >
                <option value="">Select agent...</option>
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.id.slice(0, 8)}... (E: {agent.energy.toFixed(2)})
                  </option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Or enter agent ID manually"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                disabled={!running}
              />
            </div>

            <div className="form-group">
              <label>Intervention Type</label>
              <div className="intervention-type-grid">
                {INTERVENTION_TYPES.map((type) => (
                  <button
                    key={type.value}
                    className={`intervention-btn ${type.danger ? 'danger' : ''} ${
                      interventionType === type.value ? 'selected' : ''
                    }`}
                    onClick={() => setInterventionType(type.value)}
                    disabled={!running}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            {interventionType === 'teleport' && (
              <div className="form-group">
                <label>Coordinates</label>
                <div className="coords-input">
                  <input
                    type="number"
                    placeholder="X"
                    value={parameters.x || ''}
                    onChange={(e) => setParameters({ ...parameters, x: e.target.value })}
                    disabled={!running}
                  />
                  <input
                    type="number"
                    placeholder="Y"
                    value={parameters.y || ''}
                    onChange={(e) => setParameters({ ...parameters, y: e.target.value })}
                    disabled={!running}
                  />
                </div>
              </div>
            )}

            {message && (
              <div className={`message ${message.type}`}>
                {message.text}
              </div>
            )}

            <button
              className={`execute-btn ${selectedIntervention?.danger ? 'danger' : ''}`}
              onClick={handleExecute}
              disabled={executing || !running || !targetId.trim()}
            >
              {executing ? 'Executing...' : `Execute ${interventionType.replace('_', ' ')}`}
            </button>
          </div>
        </div>
      )}

      <div className="audit-section">
        <div className="audit-header">
          <h4>Audit Log</h4>
          {god_mode_audit_log.length > 0 && (
            <button className="clear-btn" onClick={handleClearAudit}>
              Clear
            </button>
          )}
        </div>
        <div className="audit-log">
          {god_mode_audit_log.length === 0 ? (
            <div className="no-audit">No interventions recorded</div>
          ) : (
            god_mode_audit_log.slice().reverse().map((entry, idx) => (
              <div key={idx} className="audit-entry">
                <div className="audit-entry-header">
                  <span className={`audit-type ${entry.intervention_type === 'kill' ? 'danger' : ''}`}>
                    {entry.intervention_type}
                  </span>
                  <span className="audit-target">{entry.target_id.slice(0, 8)}...</span>
                </div>
                <div className="audit-entry-details">
                  <span>Tick {entry.tick}</span>
                  <span className={`audit-result ${entry.result !== 'success' ? 'error' : ''}`}>
                    {entry.result}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
