import { useEffect } from 'react'
import { useWorldStore } from '../../store/worldStore'

interface ProfilingPanelProps {
  onClose?: () => void
}

export function ProfilingPanel({ onClose }: ProfilingPanelProps) {
  const { 
    profiling_stats, 
    profiling_report, 
    fetchProfilingStats, 
    fetchProfilingReport,
    resetProfiling 
  } = useWorldStore()
  
  useEffect(() => {
    fetchProfilingStats()
    fetchProfilingReport()
    
    const interval = setInterval(() => {
      fetchProfilingStats()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [fetchProfilingStats, fetchProfilingReport])
  
  const handleReset = async () => {
    await resetProfiling()
    await fetchProfilingStats()
    await fetchProfilingReport()
  }
  
  return (
    <div className="profiling-panel">
      <div className="profiling-header">
        <h3>Profiling Stats</h3>
        <div className="profiling-actions">
          <button className="refresh-btn" onClick={() => { fetchProfilingStats(); fetchProfilingReport(); }}>
            Refresh
          </button>
          <button className="reset-btn" onClick={handleReset}>
            Reset
          </button>
          {onClose && (
            <button className="close-btn" onClick={onClose}>×</button>
          )}
        </div>
      </div>
      
      {profiling_stats && (
        <div className="profiling-summary">
          <div className="summary-stat">
            <span className="summary-label">Total Calls</span>
            <span className="summary-value">{profiling_stats.total_calls.toLocaleString()}</span>
          </div>
          <div className="summary-stat">
            <span className="summary-label">Total Time</span>
            <span className="summary-value">{profiling_stats.total_time_ms.toFixed(2)} ms</span>
          </div>
        </div>
      )}
      
      {profiling_report && profiling_report.functions.length > 0 && (
        <div className="profiling-functions">
          <h4>Function Breakdown</h4>
          <div className="functions-list">
            {profiling_report.functions.slice(0, 20).map((func, i) => (
              <div key={i} className="function-item">
                <div className="function-info">
                  <span className="function-name">{func.name}</span>
                  <span className="function-calls">{func.calls} calls</span>
                </div>
                <div className="function-stats">
                  <div className="function-time">
                    {func.total_time_ms.toFixed(2)} ms
                  </div>
                  <div className="function-bar-container">
                    <div 
                      className="function-bar"
                      style={{ width: `${Math.min(func.percentage, 100)}%` }}
                    />
                  </div>
                  <span className="function-percentage">{func.percentage.toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {(!profiling_stats || profiling_stats.total_calls === 0) && (
        <div className="no-profiling-data">
          No profiling data available. Run some simulations to collect statistics.
        </div>
      )}
    </div>
  )
}