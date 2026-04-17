import React from 'react'
import { motion } from 'framer-motion'

export function AnimatedHeatmap({ data = [], title = 'Predictive Risk Heatmap' }) {
  if (!data || data.length === 0) {
    return <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>No data available</div>
  }

  const getIntensityColor = (value) => {
    if (value >= 80) return { bg: '#DC2626', text: '#fff', intensity: 1 }
    if (value >= 60) return { bg: '#F97316', text: '#fff', intensity: 0.8 }
    if (value >= 40) return { bg: '#EAB308', text: '#000', intensity: 0.6 }
    if (value >= 20) return { bg: '#22C55E', text: '#fff', intensity: 0.4 }
    return { bg: '#10B981', text: '#fff', intensity: 0.2 }
  }

  const risks = ['Rainfall', 'Thunderstorm', 'High Wind', 'Heatwave', 'Flooding']

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20, color: '#1E293B' }}>
        {title}
      </h3>
      
      <div style={{ overflowX: 'auto' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minWidth: 600 }}>
          {/* Header */}
          <div style={{ display: 'grid', gridTemplateColumns: '120px repeat(5, 1fr)', gap: 8 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>City</div>
            {risks.map((risk) => (
              <div key={risk} style={{ fontSize: 11, fontWeight: 700, color: '#64748B', textAlign: 'center', textTransform: 'uppercase' }}>
                {risk}
              </div>
            ))}
          </div>

          {/* Data Rows */}
          {data.map((city, cityIdx) => (
            <motion.div
              key={city.city}
              style={{ display: 'grid', gridTemplateColumns: '120px repeat(5, 1fr)', gap: 8 }}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: cityIdx * 0.1 }}
            >
              <div style={{ fontSize: 13, fontWeight: 700, color: '#1E293B', paddingTop: 8 }}>
                {city.city}
              </div>
              
              {city.top_risks?.map((risk, riskIdx) => {
                const colors = getIntensityColor(risk.probability)
                return (
                  <motion.div
                    key={riskIdx}
                    style={{
                      background: colors.bg,
                      color: colors.text,
                      borderRadius: 12,
                      padding: 12,
                      textAlign: 'center',
                      fontWeight: 700,
                      fontSize: 14,
                      position: 'relative',
                      overflow: 'hidden',
                      border: `2px solid ${colors.bg}`,
                    }}
                    whileHover={{ scale: 1.05, boxShadow: '0 10px 20px rgba(0,0,0,0.15)' }}
                    transition={{ type: 'spring', stiffness: 300 }}
                  >
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${risk.probability}%` }}
                      transition={{ duration: 1.5, delay: cityIdx * 0.1 + riskIdx * 0.05 }}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        height: '100%',
                        background: 'rgba(255,255,255,0.2)',
                        borderRadius: 10,
                      }}
                    />
                    <span style={{ position: 'relative', zIndex: 1 }}>
                      {risk.probability}%
                    </span>
                  </motion.div>
                )
              })}
            </motion.div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div style={{ marginTop: 24, padding: 16, background: '#F8FAFC', borderRadius: 12, display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        {[
          { range: '80-100%', color: '#DC2626', label: 'Critical Risk' },
          { range: '60-79%', color: '#F97316', label: 'High Risk' },
          { range: '40-59%', color: '#EAB308', label: 'Medium Risk' },
          { range: '20-39%', color: '#22C55E', label: 'Low Risk' },
          { range: '0-19%', color: '#10B981', label: 'Minimal Risk' },
        ].map((item) => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 16, height: 16, borderRadius: 4, background: item.color }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: '#475569' }}>
              {item.label} ({item.range})
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
