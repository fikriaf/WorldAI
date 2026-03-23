import { useEffect } from 'react'
import { useWorldStore } from '../../store/worldStore'

export function ObserverPanel() {
  const {
    observer_enabled,
    observer_state,
    species_list,
    narrations,
    fetchObserverState,
    fetchSpeciesList,
    fetchNarrations,
    enableObserver,
    disableObserver,
    running,
  } = useWorldStore()

  useEffect(() => {
    if (running) {
      fetchObserverState()
      fetchSpeciesList()
      fetchNarrations()
      const interval = setInterval(() => {
        fetchObserverState()
        fetchSpeciesList()
        fetchNarrations()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [running, fetchObserverState, fetchSpeciesList, fetchNarrations])

  const handleToggle = () => {
    if (observer_enabled) {
      disableObserver()
    } else {
      enableObserver()
    }
  }

  return (
    <div className="observer-panel">
      <div className="observer-header">
        <h3>Observer</h3>
        <button
          className={`toggle-btn ${observer_enabled ? 'active' : ''}`}
          onClick={handleToggle}
          disabled={!running}
        >
          {observer_enabled ? 'Enabled' : 'Disabled'}
        </button>
      </div>

      {observer_enabled && (
        <>
          <div className="observer-stats">
            <div className="stat">
              <span className="stat-label">Events Processed</span>
              <span className="stat-value">{observer_state.events_processed.toLocaleString()}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Unique Species</span>
              <span className="stat-value">{observer_state.unique_species}</span>
            </div>
          </div>

          <div className="section">
            <h4>Species</h4>
            <div className="species-list">
              {species_list.length === 0 ? (
                <div className="no-data">No species data</div>
              ) : (
                species_list.map((species, i) => (
                  <div key={i} className="species-item">
                    <span className="species-name">{species.name}</span>
                    <span className="species-count">{species.count}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="section">
            <h4>Narrations</h4>
            <div className="narrations-list">
              {narrations.length === 0 ? (
                <div className="no-data">No narrations yet</div>
              ) : (
                narrations.map((narration, i) => (
                  <div key={i} className="narration-item">
                    {narration}
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}

      {!observer_enabled && running && (
        <div className="observer-disabled-msg">
          Enable the observer to track species and AI narrations
        </div>
      )}

      {!running && (
        <div className="observer-disabled-msg">
          Start the world to enable observer
        </div>
      )}
    </div>
  )
}
