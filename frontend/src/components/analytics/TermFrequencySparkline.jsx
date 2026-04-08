import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import api from '../../services/apiClient'

export function TermFrequencySparkline({ projectId }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchFrequency = async () => {
      try {
        const res = await api.get(`/${projectId}/analytics/term-frequency?limit=10`)
        if (res.data?.data) {
          // Flatten data for Recharts, showing each term's frequency over chapters
          // Not trivial to show multiple lines properly on a sparkline without preprocessing
          // For now, we just map chapter-level total occurrences if the API supports it,
          // OR we show top 5 terms and their trends.
          const formattedData = []
          const allChapters = new Set()
          const termLines = []
          
          res.data.data.forEach(term => {
            termLines.push(term.term)
            term.history.forEach(h => {
              allChapters.add(h.chapter_id)
            })
          })

          const sortedChapters = Array.from(allChapters).sort((a,b) => a-b)
          
          sortedChapters.forEach(chap => {
            const dp = { name: `Chap ${chap}` }
            res.data.data.forEach(term => {
              const hist = term.history.find(h => h.chapter_id === chap)
              dp[term.term] = hist ? hist.frequency : 0
            })
            formattedData.push(dp)
          })

          setData(formattedData)
        }
      } catch (err) {
        console.error("Failed to load frequency data", err)
      } finally {
        setLoading(false)
      }
    }
    fetchFrequency()
  }, [projectId])

  if (loading) return <div className="h-48 flex items-center justify-center">Loading Sparkline...</div>
  if (!data.length) return <div className="h-48 flex items-center justify-center text-sm text-gray-500">No narrative data available</div>

  // Create random colors for lines
  const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe']

  return (
    <div className="w-full h-64 bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Top Terms Narrative Sparkline</h3>
      <ResponsiveContainer width="100%" height="80%">
        <LineChart data={data}>
          <XAxis dataKey="name" hide />
          <YAxis hide />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
            itemStyle={{ color: '#fff' }}
          />
          {Object.keys(data[0] || {}).filter(k => k !== 'name').map((key, i) => (
            <Line 
              key={key} 
              type="monotone" 
              dataKey={key} 
              stroke={colors[i % colors.length]} 
              strokeWidth={2} 
              dot={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
