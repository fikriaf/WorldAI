type HeatmapType = 'none' | 'energy' | 'temperature' | 'chemistry' | 'reaction_diffusion'

interface ControlBarProps {
  running: boolean
  onStart: () => void
  onStop: () => void
  onStep: () => void
  onRun: () => void
  tick: number
  population: number
  heatmapType: HeatmapType
  onHeatmapChange: (type: HeatmapType) => void
  config: {
    seed_id: string
    grid_width: number
    grid_height: number
  }
  onConfigChange: (config: {
    seed_id: string
    grid_width: number
    grid_height: number
  }) => void
}

export function ControlBar({
  running,
  onStart,
  onStop,
  onStep,
  onRun,
  tick,
  population,
  heatmapType,
  onHeatmapChange,
  config,
  onConfigChange,
}: ControlBarProps) {
  return (
    <div className="control-bar">
      <div className="control-group">
        {!running ? (
          <>
            <input
              type="text"
              placeholder="Seed ID"
              value={config.seed_id}
              onChange={(e) =>
                onConfigChange({ ...config, seed_id: e.target.value })
              }
            />
            <button onClick={onStart}>Start World</button>
          </>
        ) : (
          <>
            <button onClick={onStep}>Step</button>
            <button onClick={onRun}>Run 100</button>
            <button onClick={onStop} className="danger">
              Stop
            </button>
          </>
        )}
      </div>
      <div className="control-group">
        <label>Heatmap:</label>
        <select 
          value={heatmapType}
          onChange={(e) => onHeatmapChange(e.target.value as HeatmapType)}
        >
          <option value="none">None</option>
          <option value="energy">Energy</option>
          <option value="temperature">Temperature</option>
          <option value="chemistry">Chemistry</option>
          <option value="reaction_diffusion">Reaction-Diffusion</option>
        </select>
      </div>
      <div className="status">
        <span>Tick: {tick}</span>
        <span>Pop: {population}</span>
      </div>
    </div>
  )
}