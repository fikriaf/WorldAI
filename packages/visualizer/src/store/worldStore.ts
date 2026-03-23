import { create } from 'zustand'

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

interface WorldEvent {
  tick: number
  type: string
  data: Record<string, unknown>
  timestamp: string
}

interface GridCell {
  x: number
  y: number
  chemical_pool: Record<string, number>
  temperature: number
  light_level: number
  rd_u: number
  rd_v: number
}

interface ObserverState {
  enabled: boolean
  events_processed: number
  unique_species: number
  species_labels: string[]
  recent_narrations: string[]
}

interface SpeciesInfo {
  name: string
  count: number
}

interface AuditLogEntry {
  timestamp: string
  tick: number
  intervention_type: string
  target_id: string
  user: string
  result: string
}

interface Metrics {
  tick: number
  shannon_entropy: number
  effective_complexity: number
  innovation_rate: number
  avg_neural_phi: number
  genome_diversity: number
  population: number
  species_count: number
}

interface MetricsHistoryItem {
  tick: number
  shannon_entropy: number
  effective_complexity: number
  innovation_rate: number
  avg_neural_phi: number
  genome_diversity: number
  population: number
  species_count: number
}

interface EntropyData {
  tick: number
  shannon_entropy: number
  grid_entropy: number
  agent_entropy: number
  chemical_entropy: number
}

interface ProfilingStats {
  total_calls: number
  total_time_ms: number
  functions: Record<string, {
    calls: number
    total_time_ms: number
    avg_time_ms: number
    min_time_ms: number
    max_time_ms: number
  }>
}

interface ProfilingReport {
  summary: {
    total_calls: number
    total_time_ms: number
    timestamp: string
  }
  functions: Array<{
    name: string
    calls: number
    total_time_ms: number
    avg_time_ms: number
    percentage: number
  }>
}

interface WorldState {
  tick: number
  population: number
  total_energy: number
  agents: Agent[]
  grid_data: GridCell[]
  recent_events: WorldEvent[]
  running: boolean
  world_id: string | null
  selectedAgentId: string | null
  heatmap_type: 'none' | 'energy' | 'temperature' | 'chemistry' | 'reaction_diffusion'
  observer_enabled: boolean
  observer_state: ObserverState
  species_list: SpeciesInfo[]
  narrations: string[]
  god_mode_enabled: boolean
  god_mode_audit_log: AuditLogEntry[]
  intervention_count: number
  metrics: Metrics | null
  metrics_history: MetricsHistoryItem[]
  entropy_data: EntropyData | null
  profiling_stats: ProfilingStats | null
  profiling_report: ProfilingReport | null
  
  startWorld: (config?: { seed_id?: string; grid_width?: number; grid_height?: number }) => Promise<void>
  stopWorld: () => Promise<void>
  step: () => Promise<void>
  run: (ticks?: number) => Promise<void>
  fetchState: () => Promise<void>
  selectAgent: (agentId: string | null) => void
  setHeatmapType: (type: 'none' | 'energy' | 'temperature' | 'chemistry' | 'reaction_diffusion') => void
  fetchObserverState: () => Promise<void>
  fetchSpeciesList: () => Promise<void>
  fetchNarrations: () => Promise<void>
  enableObserver: () => Promise<void>
  disableObserver: () => Promise<void>
  fetchGodModeState: () => Promise<void>
  enableGodMode: () => Promise<void>
  disableGodMode: () => Promise<void>
  performIntervention: (target_id: string, intervention_type: string, parameters?: Record<string, unknown>) => Promise<{status: string; log_entry?: AuditLogEntry}>
  fetchAuditLog: () => Promise<void>
  clearAuditLog: () => Promise<void>
  fetchMetrics: () => Promise<void>
  fetchMetricsHistory: (limit?: number) => Promise<void>
  fetchEntropy: () => Promise<void>
  fetchProfilingStats: () => Promise<void>
  fetchProfilingReport: () => Promise<void>
  resetProfiling: () => Promise<void>
}

const API_BASE = 'http://localhost:8000'

export const useWorldStore = create<WorldState>((set, get) => ({
  tick: 0,
  population: 0,
  total_energy: 0,
  agents: [],
  grid_data: [],
  recent_events: [],
  running: false,
  world_id: null,
  selectedAgentId: null,
  heatmap_type: 'none',
  observer_enabled: false,
  observer_state: {
    enabled: false,
    events_processed: 0,
    unique_species: 0,
    species_labels: [],
    recent_narrations: [],
  },
  species_list: [],
  narrations: [],
  god_mode_enabled: false,
  god_mode_audit_log: [],
  intervention_count: 0,
  metrics: null,
  metrics_history: [],
  entropy_data: null,
  profiling_stats: null,
  profiling_report: null,

  startWorld: async (config = {}) => {
    try {
      const response = await fetch(`${API_BASE}/api/world/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          seed_id: config.seed_id || 'genesis',
          grid_width: config.grid_width || 64,
          grid_height: config.grid_height || 64,
          genesis_mode: 'seeded_chemistry',
        }),
      })
      const data = await response.json()
      set({ running: true, world_id: data.world_id })
      await get().fetchState()
      await get().fetchMetrics()
      await get().fetchMetricsHistory()
    } catch (error) {
      console.error('Failed to start world:', error)
    }
  },

  stopWorld: async () => {
    try {
      await fetch(`${API_BASE}/api/world/stop`, { method: 'POST' })
      set({ running: false, world_id: null, agents: [] })
    } catch (error) {
      console.error('Failed to stop world:', error)
    }
  },

  step: async () => {
    try {
      await fetch(`${API_BASE}/api/world/step`, { method: 'POST' })
      await get().fetchState()
      await get().fetchMetrics()
      await get().fetchEntropy()
    } catch (error) {
      console.error('Failed to step:', error)
    }
  },

  run: async (ticks = 100) => {
    try {
      await fetch(`${API_BASE}/api/world/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticks }),
      })
      await get().fetchState()
      await get().fetchMetrics()
      await get().fetchMetricsHistory()
    } catch (error) {
      console.error('Failed to run:', error)
    }
  },

  fetchState: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/world/state`)
      if (response.ok) {
        const data = await response.json()
        set({
          tick: data.tick,
          population: data.population,
          total_energy: data.total_energy,
          agents: data.agents || [],
          grid_data: data.grid_data || [],
          recent_events: data.recent_events || [],
        })
      }
    } catch (error) {
      console.error('Failed to fetch state:', error)
    }
  },

  setHeatmapType: (type: 'none' | 'energy' | 'temperature' | 'chemistry' | 'reaction_diffusion') => {
    set({ heatmap_type: type })
  },

  selectAgent: (agentId) => {
    set({ selectedAgentId: agentId })
  },

  fetchObserverState: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/observer/state`)
      if (response.ok) {
        const data = await response.json()
        set({
          observer_enabled: data.enabled,
          observer_state: {
            enabled: data.enabled,
            events_processed: data.events_processed || 0,
            unique_species: data.unique_species || 0,
            species_labels: data.species_labels || [],
            recent_narrations: data.recent_narrations || [],
          },
        })
      }
    } catch (error) {
      console.error('Failed to fetch observer state:', error)
    }
  },

  fetchSpeciesList: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/observer/species`)
      if (response.ok) {
        const data = await response.json()
        set({ species_list: data.species || [] })
      }
    } catch (error) {
      console.error('Failed to fetch species list:', error)
    }
  },

  fetchNarrations: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/observer/narrations?limit=20`)
      if (response.ok) {
        const data = await response.json()
        set({ narrations: data.narrations || [] })
      }
    } catch (error) {
      console.error('Failed to fetch narrations:', error)
    }
  },

  enableObserver: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/observer/enable`, { method: 'POST' })
      if (response.ok) {
        set({ observer_enabled: true })
        await get().fetchObserverState()
      }
    } catch (error) {
      console.error('Failed to enable observer:', error)
    }
  },

  disableObserver: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/observer/disable`, { method: 'POST' })
      if (response.ok) {
        set({ observer_enabled: false })
      }
    } catch (error) {
      console.error('Failed to disable observer:', error)
    }
  },

  fetchGodModeState: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/control/godmode/state`)
      if (response.ok) {
        const data = await response.json()
        set({
          god_mode_enabled: data.enabled,
          god_mode_audit_log: data.audit_log || [],
          intervention_count: data.intervention_count || 0,
        })
      }
    } catch (error) {
      console.error('Failed to fetch god mode state:', error)
    }
  },

  enableGodMode: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/control/godmode/enable`, { method: 'POST' })
      if (response.ok) {
        set({ god_mode_enabled: true })
        await get().fetchGodModeState()
      }
    } catch (error) {
      console.error('Failed to enable god mode:', error)
    }
  },

  disableGodMode: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/control/godmode/disable`, { method: 'POST' })
      if (response.ok) {
        set({ god_mode_enabled: false })
        await get().fetchGodModeState()
      }
    } catch (error) {
      console.error('Failed to disable god mode:', error)
    }
  },

  performIntervention: async (target_id, intervention_type, parameters = {}) => {
    try {
      const response = await fetch(`${API_BASE}/api/control/intervene`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_id, intervention_type, parameters }),
      })
      const data = await response.json()
      await get().fetchGodModeState()
      await get().fetchState()
      return data
    } catch (error) {
      console.error('Failed to perform intervention:', error)
      return { status: 'error' }
    }
  },

  fetchAuditLog: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/control/audit?limit=50`)
      if (response.ok) {
        const data = await response.json()
        set({ god_mode_audit_log: data.audit_log || [] })
      }
    } catch (error) {
      console.error('Failed to fetch audit log:', error)
    }
  },

  clearAuditLog: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/control/audit`, { method: 'DELETE' })
      if (response.ok) {
        set({ god_mode_audit_log: [], intervention_count: 0 })
      }
    } catch (error) {
      console.error('Failed to clear audit log:', error)
    }
  },

  fetchMetrics: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/metrics`)
      if (response.ok) {
        const data = await response.json()
        set({ metrics: data })
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    }
  },

  fetchMetricsHistory: async (limit = 100) => {
    try {
      const response = await fetch(`${API_BASE}/api/metrics/history?limit=${limit}`)
      if (response.ok) {
        const data = await response.json()
        set({ metrics_history: data.history || [] })
      }
    } catch (error) {
      console.error('Failed to fetch metrics history:', error)
    }
  },

  fetchEntropy: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/metrics/entropy`)
      if (response.ok) {
        const data = await response.json()
        set({ entropy_data: data })
      }
    } catch (error) {
      console.error('Failed to fetch entropy:', error)
    }
  },

  fetchProfilingStats: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/profiling/stats`)
      if (response.ok) {
        const data = await response.json()
        set({ profiling_stats: data })
      }
    } catch (error) {
      console.error('Failed to fetch profiling stats:', error)
    }
  },

  fetchProfilingReport: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/profiling/report`)
      if (response.ok) {
        const data = await response.json()
        set({ profiling_report: data })
      }
    } catch (error) {
      console.error('Failed to fetch profiling report:', error)
    }
  },

  resetProfiling: async () => {
    try {
      await fetch(`${API_BASE}/api/profiling/reset`, { method: 'POST' })
      set({ profiling_stats: null, profiling_report: null })
    } catch (error) {
      console.error('Failed to reset profiling:', error)
    }
  },
}))