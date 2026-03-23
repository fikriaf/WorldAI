import { Container, Graphics } from 'pixi.js'

export type HeatmapType = 'energy' | 'temperature' | 'chemical' | 'population' | 'consciousness'

interface HeatmapCell {
  x: number
  y: number
  value: number
}

interface HeatmapLayerOptions {
  cellSize: number
  gridWidth: number
  gridHeight: number
  smoothing: boolean
  smoothingFactor: number
}

export class HeatmapLayer extends Container {
  private graphics: Graphics
  private cellSize: number
  private gridWidth: number
  private gridHeight: number
  private heatmapType: HeatmapType = 'energy'
  private visible: boolean = true
  private opacity: number = 0.5
  private smoothing: boolean = true
  private smoothingFactor: number = 0.2

  private static readonly HEATMAP_CONFIGS: Record<HeatmapType, { minColor: number; maxColor: number; valueRange: [number, number] }> = {
    energy: {
      minColor: 0x0000ff,
      maxColor: 0xff0000,
      valueRange: [0, 1],
    },
    temperature: {
      minColor: 0x00ffff,
      maxColor: 0xff4400,
      valueRange: [0, 100],
    },
    chemical: {
      minColor: 0x00ff00,
      maxColor: 0xff00ff,
      valueRange: [0, 10],
    },
    population: {
      minColor: 0x001122,
      maxColor: 0xffaa00,
      valueRange: [0, 20],
    },
    consciousness: {
      minColor: 0x110022,
      maxColor: 0xff00ff,
      valueRange: [0, 1],
    },
  }

  constructor(options: Partial<HeatmapLayerOptions> = {}) {
    super()
    this.cellSize = options.cellSize ?? 16
    this.gridWidth = options.gridWidth ?? 64
    this.gridHeight = options.gridHeight ?? 64
    this.smoothing = options.smoothing ?? true
    this.smoothingFactor = options.smoothingFactor ?? 0.2
    
    this.graphics = new Graphics()
    this.graphics.zIndex = 1
    this.addChild(this.graphics)
  }

  setHeatmapType(type: HeatmapType): void {
    this.heatmapType = type
    this.render()
  }

  setOpacity(opacity: number): void {
    this.opacity = Math.max(0, Math.min(1, opacity))
    this.render()
  }

  setVisible(visible: boolean): void {
    this.visible = visible
    this.graphics.visible = visible
  }

  toggle(): void {
    this.setVisible(!this.visible)
  }

  render(cells?: HeatmapCell[]): void {
    this.graphics.clear()
    
    if (!this.visible) return
    
    const config = HeatmapLayer.HEATMAP_CONFIGS[this.heatmapType]
    const [minVal, maxVal] = config.valueRange
    
    const normalizedCells = this.normalizeCells(cells ?? [], minVal, maxVal)
    const smoothedCells = this.smoothing ? this.applySmoothing(normalizedCells) : normalizedCells
    
    for (const cell of smoothedCells) {
      const color = this.interpolateColor(config.minColor, config.maxColor, cell.value)
      const alpha = this.opacity * cell.value
      
      this.graphics.rect(
        cell.x * this.cellSize,
        cell.y * this.cellSize,
        this.cellSize,
        this.cellSize
      )
      this.graphics.fill({ color, alpha: Math.max(0.1, alpha) })
    }
  }

  private normalizeCells(cells: HeatmapCell[], min: number, max: number): HeatmapCell[] {
    const range = max - min
    return cells.map(cell => ({
      ...cell,
      value: Math.max(0, Math.min(1, (cell.value - min) / range)),
    }))
  }

  private applySmoothing(cells: HeatmapCell[]): HeatmapCell[] {
    const grid = new Map<string, number>()
    
    for (const cell of cells) {
      grid.set(`${cell.x},${cell.y}`, cell.value)
    }
    
    const smoothed: HeatmapCell[] = []
    const width = this.gridWidth
    const height = this.gridHeight
    
    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        let sum = 0
        let count = 0
        
        for (let dx = -1; dx <= 1; dx++) {
          for (let dy = -1; dy <= 1; dy++) {
            const nx = x + dx
            const ny = y + dy
            if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
              const val = grid.get(`${nx},${ny}`)
              if (val !== undefined) {
                const weight = dx === 0 && dy === 0 ? 1 : this.smoothingFactor
                sum += val * weight
                count += weight
              }
            }
          }
        }
        
        const currentVal = grid.get(`${x},${y}`) ?? 0
        const smoothedVal = count > 0 ? sum / count : currentVal
        
        smoothed.push({ x, y, value: smoothedVal })
      }
    }
    
    return smoothed
  }

  private interpolateColor(color1: number, color2: number, t: number): number {
    const r1 = (color1 >> 16) & 0xff
    const g1 = (color1 >> 8) & 0xff
    const b1 = color1 & 0xff
    
    const r2 = (color2 >> 16) & 0xff
    const g2 = (color2 >> 8) & 0xff
    const b2 = color2 & 0xff
    
    const r = Math.floor(r1 + (r2 - r1) * t)
    const g = Math.floor(g1 + (g2 - g1) * t)
    const b = Math.floor(b1 + (b2 - b1) * t)
    
    return (r << 16) | (g << 8) | b
  }

  destroy(): void {
    this.graphics.destroy()
    super.destroy()
  }
}