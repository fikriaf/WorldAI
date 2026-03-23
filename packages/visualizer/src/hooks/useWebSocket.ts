import { useEffect, useRef, useCallback } from 'react'

interface WSMessage {
  type: string
  tick?: number
  population?: number
  total_energy?: number
  agents?: Agent[]
  recent_events?: WorldEvent[]
  timestamp?: string
}

interface Agent {
  id: string
  position_x: number
  position_y: number
  velocity_x?: number
  velocity_y?: number
  energy: number
  health: number
  age_ticks: number
  stage: string
  genome_hash: string
  genes_count?: number
  species_label?: string
  parent_count?: number
  children_count?: number
}

interface WorldEvent {
  tick: number
  type: string
  data: Record<string, unknown>
  timestamp: string
}

export function useWebSocket(
  url: string,
  onMessage?: (message: WSMessage) => void,
  onConnect?: () => void,
  onDisconnect?: () => void
) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number>()

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    const ws = new WebSocket(url)

    ws.onopen = () => {
      console.log('WebSocket connected')
      onConnect?.()
      
      ws.send(JSON.stringify({ type: 'subscribe_state' }))
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSMessage
        onMessage?.(message)
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      onDisconnect?.()
      
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect()
      }, 3000)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    wsRef.current = ws
  }, [url, onMessage, onConnect, onDisconnect])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const send = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  const subscribeState = useCallback(() => {
    send({ type: 'subscribe_state' })
  }, [send])

  const requestState = useCallback(() => {
    send({ type: 'get_state' })
  }, [send])

  const setSpeed = useCallback((speed: number) => {
    send({ type: 'set_speed', speed })
  }, [send])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    connect,
    disconnect,
    send,
    subscribeState,
    requestState,
    setSpeed,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  }
}
