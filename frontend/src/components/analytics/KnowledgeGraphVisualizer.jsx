import React, { useState, useEffect } from 'react'
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import api from '../../services/apiClient'

export function KnowledgeGraphVisualizer({ projectId }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const res = await api.get(`/graph/${projectId}/timeline`)
        if (res.data?.timeline) {
          // Parse relationships to nodes and edges.
          // Using a force-directed layout manually is tough, so we'll just arrange them in a simple grid
          // or use dagre if installed. For now, random/grid positioning on initialize.
          const newNodes = []
          const newEdges = []
          const addedNodes = new Set()

          // We'll just look at the latest timeline snapshot or aggregate
          // The timeline API returns { chapter: N, active_relationships: [...] }
          // Let's aggregate all active relationships in the latest chapter
          const latestSnap = res.data.timeline[res.data.timeline.length - 1]
          if (!latestSnap) return

          let x = 0; let y = 0;
          latestSnap.active_relationships.forEach((rel) => {
            if (!addedNodes.has(rel.source_id)) {
              newNodes.push({
                id: `node-${rel.source_id}`,
                data: { label: rel.source_term },
                position: { x: (x % 5) * 150, y: Math.floor(x / 5) * 100 },
                style: { background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '10px' }
              })
              addedNodes.add(rel.source_id)
              x++
            }
            if (!addedNodes.has(rel.target_id)) {
              newNodes.push({
                id: `node-${rel.target_id}`,
                data: { label: rel.target_term },
                position: { x: (y % 5) * 150, y: Math.floor(y / 5) * 100 + 50 },
                style: { background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '10px' }
              })
              addedNodes.add(rel.target_id)
              y++
            }

            newEdges.push({
              id: `edge-${rel.id}`,
              source: `node-${rel.source_id}`,
              target: `node-${rel.target_id}`,
              label: rel.relation_type,
              animated: false,
              markerEnd: { type: MarkerType.ArrowClosed }
            })
          })

          setNodes(newNodes)
          setEdges(newEdges)
        }
      } catch (err) {
        console.error("Failed to load Knowledge Graph", err)
      } finally {
        setLoading(false)
      }
    }
    fetchGraph()
  }, [projectId, setNodes, setEdges])

  if (loading) return <div className="h-96 flex items-center justify-center">Loading Knowledge Graph...</div>

  return (
    <div className="w-full h-[500px] border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden bg-gray-50 dark:bg-gray-900">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <MiniMap />
        <Controls />
        <Background gap={12} size={1} />
      </ReactFlow>
    </div>
  )
}
