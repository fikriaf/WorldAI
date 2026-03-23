import { Container, Graphics } from 'pixi.js'

export type CAType = 'game_of_life' | 'wireworld'

interface CACell {
  x: number
  y: number
  state: number
}

interface CALayerOptions {
  cellSize: number
  gridWidth: number
  gridHeight: number
  overlay: boolean
}

export class CALayer extends Container {
  private graphics: Graphics
  private cellSize: number
  private gridWidth: number
  private gridHeight: number
  private caType: CAType = 'game_of_life'
  private visible: boolean = true
  private overlay: boolean = true
  private cells: CACell[] = []

  private static readonly GOL_COLORS: Record<number, number> = {
    0: 0x000000,
    1: 0x00ff88,
  }

  private static readonly WIREWORLD_COLORS: Record<number, number> = {
    0: 0x111111,
    1: 0x000000,
    2: 0xff0000,
    3: 0x0000ff,
    4: 0xffff00,
  }

  constructor(options: Partial<CALayerOptions> = {}) {
    super()
    this.cellSize = options.cellSize ?? 8
    this.gridWidth = options.gridWidth ?? 64
    this.gridHeight = options.gridHeight ?? 64
    this.overlay = options.overlay ?? true
    
    this.graphics = new Graphics()
    this.graphics.zIndex = this.overlay ? 2 : 0
    this.addChild(this.graphics)
  }

  setCAType(type: CAType): void {
    this.caType = type
    this.render()
  }

  setVisible(visible: boolean): void {
    this.visible = visible
    this.graphics.visible = visible
  }

  toggle(): void {
    this.setVisible(!this.visible)
  }

  setCells(cells: CACell[]): void {
    this.cells = cells
    this.render()
  }

  updateGOL(): void {
    if (this.caType !== 'game_of_life') return
    
    const grid = this.buildGrid()
    const nextGen: CACell[] = []
    const width = this.gridWidth
    const height = this.gridHeight
    
    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        const neighbors = this.countNeighbors(grid, x, y, width, height)
        const alive = grid.get(`${x},${y}`) === 1
        
        let nextState = 0
        if (alive && (neighbors === 2 || neighbors === 3)) {
          nextState = 1
        } else if (!alive && neighbors === 3) {
          nextState = 1
        }
        
        nextGen.push({ x, y, state: nextState })
      }
    }
    
    this.cells = nextGen
    this.render()
  }

  updateWireworld(): void {
    if (this.caType !== 'wireworld') return
    
    const grid = this.buildGrid()
    const nextGen: CACell[] = []
    const width = this.gridWidth
    const height = this.gridHeight
    
    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        const state = grid.get(`${x},${y}`) ?? 0
        let nextState = state
        
        if (state === 1) {
          nextState = 2
        } else if (state === 2) {
          const electronHeads = this.countWireworldHeads(grid, x, y, width, height)
          if (electronHeads === 1 || electronHeads === 2) {
            nextState = 3
          }
        } else if (state === 3) {
          nextState = 1
        }
        
        nextGen.push({ x, y, state: nextState })
      }
    }
    
    this.cells = nextGen
    this.render()
  }

  render(): void {
    this.graphics.clear()
    
    if (!this.visible) return
    
    const colors = this.caType === 'game_of_life' 
      ? CALayer.GOL_COLORS 
      : CALayer.WIREWORLD_COLORS
    
    for (const cell of this.cells) {
      const color = colors[cell.state] ?? 0x000000
      
      this.graphics.rect(
        cell.x * this.cellSize,
        cell.y * this.cellSize,
        this.cellSize,
        this.cellSize
      )
      
      if (cell.state !== 0) {
        this.graphics.fill({ color, alpha: 0.9 })
      } else {
        this.graphics.fill({ color, alpha: 0.05 })
      }
    }
    
    this.graphics.stroke({ width: 0.5, color: 0x333333, alpha: 0.3 })
  }

  private buildGrid(): Map<string, number> {
    const grid = new Map<string, number>()
    for (const cell of this.cells) {
      grid.set(`${cell.x},${cell.y}`, cell.state)
    }
    return grid
  }

  private countNeighbors(grid: Map<string, number>, x: number, y: number, width: number, height: number): number {
    let count = 0
    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        if (dx === 0 && dy === 0) continue
        const nx = (x + dx + width) % width
        const ny = (y + dy + height) % height
        if (grid.get(`${nx},${ny}`) === 1) {
          count++
        }
      }
    }
    return count
  }

  private countWireworldHeads(grid: Map<string, number>, x: number, y: number, width: number, height: number): number {
    let count = 0
    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        if (dx === 0 && dy === 0) continue
        const nx = x + dx
        const ny = y + dy
        if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
          if (grid.get(`${nx},${ny}`) === 3) {
            count++
          }
        }
      }
    }
    return count
  }

  destroy(): void {
    this.graphics.destroy()
    super.destroy()
  }
}