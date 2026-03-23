import { useEffect, useRef, useState } from 'react'
import * as PIXI from 'pixi.js'

interface Agent {
  id: string
  position_x: number
  position_y: number
  velocity_x?: number
  velocity_y?: number
  energy: number
  health: number
  stage: string
  genome_hash: string
  species_label?: string
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

interface WorldRendererProps {
  agents: Agent[]
  gridData?: GridCell[]
  onAgentClick?: (agentId: string) => void
  showTrails?: boolean
  trailLength?: number
  heatmapType?: 'none' | 'energy' | 'temperature' | 'chemistry' | 'reaction_diffusion'
}

interface TrailPoint {
  x: number
  y: number
  age: number
}

const GRID_SIZE = 64

export function WorldRenderer({ 
  agents, 
  gridData,
  onAgentClick, 
  showTrails = true, 
  trailLength = 30,
  heatmapType = 'none'
}: WorldRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const appRef = useRef<PIXI.Application | null>(null)
  const spritesRef = useRef<Map<string, PIXI.Graphics>>(new Map())
  const trailsRef = useRef<Map<string, TrailPoint[]>>(new Map())
  const trailGraphicsRef = useRef<PIXI.Graphics | null>(null)
  const heatmapGraphicsRef = useRef<PIXI.Graphics | null>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        setDimensions({ width: Math.floor(width), height: Math.floor(height) })
      }
    })

    resizeObserver.observe(container)

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  useEffect(() => {
    if (!containerRef.current || appRef.current) return

    let mounted = true

    const initPixi = async () => {
      if (!mounted || !containerRef.current) return

      const app = new PIXI.Application()
      
      await app.init({
        width: dimensions.width,
        height: dimensions.height,
        backgroundColor: 0x0a0a0f,
        antialias: true,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true,
      })

      if (!mounted || !containerRef.current) {
        app.destroy(true, { children: true })
        return
      }

      containerRef.current.appendChild(app.canvas as HTMLCanvasElement)
      appRef.current = app

      const graphics = new PIXI.Graphics()
      
      const cellWidth = dimensions.width / GRID_SIZE
      const cellHeight = dimensions.height / GRID_SIZE
      
      graphics.stroke({ width: 0.5, color: 0x1a1a2e, alpha: 0.3 })
      
      for (let x = 0; x <= GRID_SIZE; x++) {
        graphics.moveTo(x * cellWidth, 0)
        graphics.lineTo(x * cellWidth, dimensions.height)
      }
      
      for (let y = 0; y <= GRID_SIZE; y++) {
        graphics.moveTo(0, y * cellHeight)
        graphics.lineTo(dimensions.width, y * cellHeight)
      }
      
      app.stage.addChild(graphics)

      if (showTrails) {
        trailGraphicsRef.current = new PIXI.Graphics()
        app.stage.addChildAt(trailGraphicsRef.current, 0)
      }

      if (heatmapType !== 'none') {
        heatmapGraphicsRef.current = new PIXI.Graphics()
        app.stage.addChildAt(heatmapGraphicsRef.current, 0)
      }
    }

    initPixi()

    return () => {
      mounted = false
      if (appRef.current) {
        appRef.current.destroy(true, { children: true })
        appRef.current = null
      }
    }
  }, [dimensions, showTrails])

  useEffect(() => {
    if (!appRef.current) return

    const app = appRef.current
    const sprites = spritesRef.current
    const trails = trailsRef.current
    const containerWidth = dimensions.width
    const containerHeight = dimensions.height
    const handleClick = onAgentClick || (() => {})

    const existingIds = new Set(sprites.keys())
    const newIds = new Set(agents.map(a => a.id))

    for (const id of existingIds) {
      if (!newIds.has(id)) {
        const sprite = sprites.get(id)
        if (sprite) {
          app.stage.removeChild(sprite)
          sprites.delete(id)
        }
        trails.delete(id)
      }
    }

    if (showTrails && trailGraphicsRef.current) {
      const trailGraphics = trailGraphicsRef.current
      trailGraphics.clear()

      for (const [_agentId, trailPoints] of trails) {
        if (trailPoints.length < 2) continue

        for (let i = 1; i < trailPoints.length; i++) {
          const p1 = trailPoints[i - 1]
          const p2 = trailPoints[i]
          
          trailGraphics.moveTo(
            (p1.x / GRID_SIZE) * containerWidth,
            (p1.y / GRID_SIZE) * containerHeight
          )
          trailGraphics.lineTo(
            (p2.x / GRID_SIZE) * containerWidth,
            (p2.y / GRID_SIZE) * containerHeight
          )
        }
      }
      
      trailGraphics.stroke({ width: 1, color: 0x00ff88, alpha: 0.3 })
    }

    for (const agent of agents) {
      let trail = trails.get(agent.id)
      if (!trail) {
        trail = []
        trails.set(agent.id, trail)
      }

      if (showTrails) {
        trail.push({
          x: agent.position_x,
          y: agent.position_y,
          age: 0,
        })

        while (trail.length > trailLength) {
          trail.shift()
        }
      }

      let sprite = sprites.get(agent.id)
      
      if (!sprite) {
        sprite = new PIXI.Graphics()
        
        const energyColor = agent.energy > 0.7 ? 0x00ff88 : 
                           agent.energy > 0.4 ? 0xffff00 : 0xff4444
        
        sprite.circle(0, 0, 4)
        sprite.fill({ color: energyColor, alpha: 0.9 })
        
        sprite.stroke({ width: 1, color: 0xffffff, alpha: 0.5 })
        
        sprite.eventMode = 'static'
        sprite.cursor = 'pointer'
        sprite.on('pointerdown', () => handleClick(agent.id))
        
        app.stage.addChild(sprite)
        sprites.set(agent.id, sprite)
      } else {
        sprite.clear()
        
        const energyColor = agent.energy > 0.7 ? 0x00ff88 : 
                           agent.energy > 0.4 ? 0xffff00 : 0xff4444
        
        sprite.circle(0, 0, 4)
        sprite.fill({ color: energyColor, alpha: 0.9 })
        
        sprite.stroke({ width: 1, color: 0xffffff, alpha: 0.5 })
      }

      sprite.x = (agent.position_x / GRID_SIZE) * containerWidth
      sprite.y = (agent.position_y / GRID_SIZE) * containerHeight
    }

    if (showTrails && trailGraphicsRef.current) {
      trailGraphicsRef.current.stroke({ width: 1, color: 0x00ff88, alpha: 0.3 })
    }
  }, [agents, dimensions, onAgentClick, showTrails, trailLength])

  useEffect(() => {
    if (!appRef.current || !heatmapGraphicsRef.current || !gridData || heatmapType === 'none') {
      return
    }

    const heatmapGraphics = heatmapGraphicsRef.current
    heatmapGraphics.clear()

    const cellWidth = dimensions.width / GRID_SIZE
    const cellHeight = dimensions.height / GRID_SIZE

    const gridMap = new Map<string, GridCell>()
    for (const cell of gridData) {
      gridMap.set(`${cell.x},${cell.y}`, cell)
    }

    for (let x = 0; x < GRID_SIZE; x++) {
      for (let y = 0; y < GRID_SIZE; y++) {
        const cell = gridMap.get(`${x},${y}`)
        if (!cell) continue

        let value = 0
        switch (heatmapType) {
          case 'energy':
            value = Object.values(cell.chemical_pool).reduce((a, b) => a + b, 0) / 10
            break
          case 'temperature':
            value = cell.temperature / 100
            break
          case 'chemistry':
            value = (cell.chemical_pool['P'] || 0) / 5
            break
          case 'reaction_diffusion':
            value = cell.rd_u
            break
        }

        value = Math.max(0, Math.min(1, value))

        const r = Math.floor(value * 255)
        const g = Math.floor((1 - value) * 128)
        const b = Math.floor(255 - value * 200)
        const color = (r << 16) | (g << 8) | b

        heatmapGraphics.rect(x * cellWidth, y * cellHeight, cellWidth, cellHeight)
        heatmapGraphics.fill({ color, alpha: 0.4 })
      }
    }
  }, [gridData, heatmapType, dimensions.width, dimensions.height])

  return (
    <div
      ref={containerRef}
      className="world-renderer"
      style={{ width: '100%', height: '100%' }}
    />
  )
}
