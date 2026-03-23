import { useState, useCallback } from 'react'

interface CameraState {
  x: number
  y: number
  zoom: number
}

interface CameraControlsProps {
  gridWidth: number
  gridHeight: number
  onCameraChange?: (camera: CameraState) => void
}

export function CameraControls({ 
  gridWidth, 
  gridHeight,
  onCameraChange 
}: CameraControlsProps) {
  const [camera, setCamera] = useState<CameraState>({
    x: gridWidth / 2,
    y: gridHeight / 2,
    zoom: 1
  })

  const move = useCallback((dx: number, dy: number) => {
    setCamera(prev => {
      const newCamera = {
        ...prev,
        x: Math.max(0, Math.min(gridWidth, prev.x + dx)),
        y: Math.max(0, Math.min(gridHeight, prev.y + dy))
      }
      onCameraChange?.(newCamera)
      return newCamera
    })
  }, [gridWidth, gridHeight, onCameraChange])

  const zoom = useCallback((delta: number) => {
    setCamera(prev => {
      const newCamera = {
        ...prev,
        zoom: Math.max(0.25, Math.min(4, prev.zoom + delta))
      }
      onCameraChange?.(newCamera)
      return newCamera
    })
  }, [onCameraChange])

  const reset = useCallback(() => {
    setCamera({ x: gridWidth / 2, y: gridHeight / 2, zoom: 1 })
    onCameraChange?.({ x: gridWidth / 2, y: gridHeight / 2, zoom: 1 })
  }, [gridWidth, gridHeight, onCameraChange])

  return (
    <div className="camera-controls">
      <div className="camera-dpad">
        <button className="up" onClick={() => move(0, -1)}>▲</button>
        <button className="left" onClick={() => move(-1, 0)}>◀</button>
        <button className="center" onClick={reset}>⊙</button>
        <button className="right" onClick={() => move(1, 0)}>▶</button>
        <button className="down" onClick={() => move(0, 1)}>▼</button>
      </div>
      
      <div className="camera-zoom">
        <button onClick={() => zoom(-0.25)}>-</button>
        <span>{camera.zoom.toFixed(2)}x</span>
        <button onClick={() => zoom(0.25)}>+</button>
      </div>
      
      <div className="camera-coords">
        X: {camera.x.toFixed(0)} Y: {camera.y.toFixed(0)}
      </div>
    </div>
  )
}

export function useCamera(gridWidth: number, gridHeight: number) {
  const [camera, setCamera] = useState<CameraState>({
    x: gridWidth / 2,
    y: gridHeight / 2,
    zoom: 1
  })

  const screenToWorld = useCallback((screenX: number, screenY: number, containerWidth: number, containerHeight: number) => {
    const cellWidth = containerWidth / gridWidth / camera.zoom
    const cellHeight = containerHeight / gridHeight / camera.zoom
    
    return {
      x: camera.x - (containerWidth / 2 - screenX) / cellWidth,
      y: camera.y - (containerHeight / 2 - screenY) / cellHeight
    }
  }, [camera, gridWidth, gridHeight])

  const worldToScreen = useCallback((worldX: number, worldY: number, containerWidth: number, containerHeight: number) => {
    const cellWidth = containerWidth / gridWidth / camera.zoom
    const cellHeight = containerHeight / gridHeight / camera.zoom
    
    return {
      x: (worldX - camera.x) * cellWidth + containerWidth / 2,
      y: (worldY - camera.y) * cellHeight + containerHeight / 2
    }
  }, [camera, gridWidth, gridHeight])

  return { camera, setCamera, screenToWorld, worldToScreen }
}