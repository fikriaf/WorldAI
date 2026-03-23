import { useMemo } from 'react'

interface Gene {
  id: string
  name: string
  sequence: string
  expressionLevel: number
  isMutated: boolean
  epigeneticMarks: string[]
}

interface GenomeVizProps {
  genes?: Gene[]
  checksum?: string
  onGeneClick?: (geneId: string) => void
}

export function GenomeViz({
  genes = [],
  checksum = '',
  onGeneClick,
}: GenomeVizProps) {
  const geneSequence = useMemo(() => {
    return genes.map(g => g.sequence).join('')
  }, [genes])

  const shortChecksum = useMemo(() => {
    if (!checksum) return ''
    return checksum.slice(0, 16) + (checksum.length > 16 ? '...' : '')
  }, [checksum])

  return (
    <div className="genome-viz">
      <div className="genome-header">
        <h4>Genome</h4>
        {checksum && (
          <div className="checksum">
            <span className="checksum-label">Checksum:</span>
            <span className="checksum-value">{shortChecksum}</span>
          </div>
        )}
      </div>

      <div className="gene-sequence">
        <div className="sequence-label">Sequence</div>
        <div className="sequence-display">
          {geneSequence ? (
            <span className="sequence-text">
              {geneSequence.slice(0, 100)}
              {geneSequence.length > 100 && '...'}
            </span>
          ) : (
            <span className="empty-sequence">No gene data</span>
          )}
        </div>
      </div>

      <div className="genes-list">
        <div className="genes-label">Genes ({genes.length})</div>
        {genes.length === 0 ? (
          <div className="empty-state">No genes</div>
        ) : (
          <div className="genes-scroll">
            {genes.map((gene) => (
              <div
                key={gene.id}
                className={`gene-item ${gene.isMutated ? 'mutated' : ''}`}
                onClick={() => onGeneClick?.(gene.id)}
              >
                <div className="gene-header">
                  <span className="gene-name">{gene.name}</span>
                  {gene.isMutated && (
                    <span className="mutation-badge">MUTATED</span>
                  )}
                </div>
                <div className="gene-sequence-small">
                  {gene.sequence.slice(0, 20)}
                  {gene.sequence.length > 20 && '...'}
                </div>
                <div className="expression-container">
                  <div className="expression-label">Expression</div>
                  <div className="expression-bar-bg">
                    <div
                      className="expression-bar"
                      style={{ width: `${gene.expressionLevel * 100}%` }}
                    />
                  </div>
                  <span className="expression-value">
                    {(gene.expressionLevel * 100).toFixed(1)}%
                  </span>
                </div>
                {gene.epigeneticMarks.length > 0 && (
                  <div className="epigenetic-marks">
                    {gene.epigeneticMarks.map((mark, i) => (
                      <span key={i} className="mark" title={mark}>
                        {mark.slice(0, 3)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="genome-stats">
        <div className="stat">
          <span className="stat-label">Total Genes:</span>
          <span className="stat-value">{genes.length}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Mutations:</span>
          <span className="stat-value">
            {genes.filter(g => g.isMutated).length}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Avg Expression:</span>
          <span className="stat-value">
            {genes.length > 0
              ? (genes.reduce((sum, g) => sum + g.expressionLevel, 0) / genes.length * 100).toFixed(1)
              : 0}%
          </span>
        </div>
      </div>
    </div>
  )
}