import { Container, Graphics, Text, BlurFilter } from 'pixi.js'

export type AgentStage = 'embryo' | 'larva' | 'adult' | 'elder' | 'decayed'
export type EmotionType = 'neutral' | 'happy' | 'angry' | 'scared' | 'curious'

interface AgentSpriteOptions {
  id: string
  positionX: number
  positionY: number
  energy: number
  health: number
  age: number
  stage: AgentStage
  speciesLabel?: string
  genomeHash: string
  mass: number
  neuralComplexity: number
  dominantEmotion: EmotionType
  groupId?: string
  isConscious?: boolean
}

export class AgentSprite extends Container {
  private id: string
  private body: Graphics
  private glow: Graphics
  private label?: Text
  private border: Graphics
  private emotionTint: number

  private static readonly STAGE_COLORS: Record<AgentStage, number> = {
    embryo: 0x9966ff,
    larva: 0xffaa00,
    adult: 0x00ff88,
    elder: 0x88aaff,
    decayed: 0x666666,
  }

  private static readonly EMOTION_TINTS: Record<EmotionType, number> = {
    neutral: 0xffffff,
    happy: 0xffff99,
    angry: 0xff6666,
    scared: 0x6666ff,
    curious: 0x66ffff,
  }

  private static readonly GROUP_BORDER_COLORS: string[] = [
    0xff6b6b, 0x4ecdc4, 0x45b7d1, 0xf9ca24, 0x6c5ce7,
    0xa29bfe, 0xfd79a8, 0x00b894, 0xe17055, 0x74b9ff,
  ]

  constructor(options: AgentSpriteOptions) {
    super()
    this.id = options.id
    this.emotionTint = AgentSprite.EMOTION_TINTS[options.dominantEmotion]
    
    this.glow = new Graphics()
    this.body = new Graphics()
    this.border = new Graphics()
    
    this.sortableChildren = true
    this.zIndex = 10
    
    this.setupSprite(options)
  }

  private setupSprite(options: AgentSpriteOptions): void {
    const baseSize = 4 + Math.sqrt(options.mass) * 2
    const complexitySize = options.neuralComplexity * 3
    const totalRadius = baseSize + complexitySize
    
    this.drawGlow(totalRadius, options.isConscious || false, options.neuralComplexity)
    this.drawBody(baseSize, options)
    this.drawBorder(options.groupId)
    this.drawLabel(options, totalRadius)
  }

  private drawGlow(radius: number, isConscious: boolean, complexity: number): void {
    this.glow.clear()
    
    if (!isConscious && complexity < 0.5) return
    
    const glowAlpha = isConscious ? 0.4 : Math.min(0.3, complexity * 0.3)
    const glowRadius = radius + 8
    
    this.glow.circle(0, 0, glowRadius)
    this.glow.fill({ color: this.emotionTint, alpha: glowAlpha })
    
    if (isConscious) {
      const blurFilter = new BlurFilter(8)
      this.glow.filters = [blurFilter]
    }
    
    this.glow.zIndex = 5
    this.addChild(this.glow)
  }

  private drawBody(radius: number, options: AgentSpriteOptions): void {
    this.body.clear()
    
    const stageColor = AgentSprite.STAGE_COLORS[options.stage]
    const energyFactor = options.energy
    
    const r = ((stageColor >> 16) & 0xff) * energyFactor + ((this.emotionTint >> 16) & 0xff) * (1 - energyFactor)
    const g = ((stageColor >> 8) & 0xff) * energyFactor + ((this.emotionTint >> 8) & 0xff) * (1 - energyFactor)
    const b = (stageColor & 0xff) * energyFactor + (this.emotionTint & 0xff) * (1 - energyFactor)
    
    const color = (Math.floor(r) << 16) | (Math.floor(g) << 8) | Math.floor(b)
    
    this.body.circle(0, 0, radius)
    this.body.fill({ color, alpha: 0.9 })
    
    this.body.stroke({ width: 1.5, color: 0xffffff, alpha: 0.6 })
    
    this.body.zIndex = 10
    this.addChild(this.body)
  }

  private drawBorder(groupId?: string): void {
    this.border.clear()
    
    if (!groupId) return
    
    const hash = this.hashString(groupId)
    const colorIndex = hash % AgentSprite.GROUP_BORDER_COLORS.length
    const borderColor = AgentSprite.GROUP_BORDER_COLORS[colorIndex]
    
    this.border.circle(0, 0, 8)
    this.border.stroke({ width: 2, color: borderColor, alpha: 0.8 })
    
    this.border.zIndex = 15
    this.addChild(this.border)
  }

  private drawLabel(options: AgentSpriteOptions, radius: number): void {
    if (options.neuralComplexity < 0.7) return
    
    this.label = new Text({
      text: options.speciesLabel || options.id.slice(0, 6),
      style: {
        fontSize: 10,
        fill: 0xffffff,
        alpha: Math.min(1, options.neuralComplexity),
      },
    })
    
    this.label.y = -radius - 12
    this.label.x = -this.label.width / 2
    this.label.zIndex = 20
    this.addChild(this.label)
  }

  private hashString(str: string): number {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0
    }
    return Math.abs(hash)
  }

  update(options: Partial<AgentSpriteOptions> & { positionX: number; positionY: number }): void {
    this.x = options.positionX
    this.y = options.positionY
    
    if (options.energy !== undefined || options.health !== undefined || options.dominantEmotion !== undefined) {
      this.body.clear()
      
      const energy = options.energy ?? this.getCurrentEnergy()
      const stageColor = AgentSprite.STAGE_COLORS[options.stage as AgentStage || 'adult']
      const emotionTint = options.dominantEmotion ? AgentSprite.EMOTION_TINTS[options.dominantEmotion] : this.emotionTint
      
      const energyFactor = energy
      const r = ((stageColor >> 16) & 0xff) * energyFactor + ((emotionTint >> 16) & 0xff) * (1 - energyFactor)
      const g = ((stageColor >> 8) & 0xff) * energyFactor + ((emotionTint >> 8) & 0xff) * (1 - energyFactor)
      const b = (stageColor & 0xff) * energyFactor + (emotionTint & 0xff) * (1 - energyFactor)
      
      const color = (Math.floor(r) << 16) | (Math.floor(g) << 8) | Math.floor(b)
      
      const mass = options.mass ?? 10
      const baseSize = 4 + Math.sqrt(mass) * 2
      
      this.body.circle(0, 0, baseSize)
      this.body.fill({ color, alpha: 0.9 })
      this.body.stroke({ width: 1.5, color: 0xffffff, alpha: 0.6 })
    }
  }

  private getCurrentEnergy(): number {
    return 0.5
  }

  destroy(): void {
    if (this.label) {
      this.label.destroy()
    }
    super.destroy()
  }
}