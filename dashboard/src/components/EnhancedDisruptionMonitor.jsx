import React from 'react'
import { motion } from 'framer-motion'
import { Zap, AlertCircle } from 'lucide-react'

export function EnhancedDisruptionMonitor({ disruptions = [], liveCount = 0 }) {
  const getSeverityConfig = (severity) => {
    switch (severity) {
      case 'extreme':
        return { bg: '#FEF2F2', color: '#DC2626', bgLight: '#FEE2E2', pulse: '#EF4444' }
      case 'severe':
        return { bg: '#FFFBEB', color: '#D97706', bgLight: '#FEF3C7', pulse: '#F59E0B' }
      case 'moderate':
        return { bg: '#EFF6FF', color: '#2563EB', bgLight: '#DBEAFE', pulse: '#3B82F6' }
      default:
        return { bg: '#F0FDF4', color: '#16A34A', bgLight: '#DCFCE7', pulse: '#22C55E' }
    }
  }

  const containerVariants = {
    initial: { opacity: 0 },
    animate: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  }

  const itemVariants = {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: '#1E293B', flex: 1 }}>
          Live Disruption Monitor
        </h3>
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 13,
            fontWeight: 700,
            background: '#ECFDF5',
            color: '#10B981',
            padding: '6px 12px',
            borderRadius: 20,
          }}
        >
          <motion.div
            animate={{ scale: [1, 1.5, 1], opacity: [1, 0.3, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#10B981',
              boxShadow: '0 0 12px #10B981',
            }}
          />
          Tracking {liveCount} events
        </motion.div>
      </div>

      {disruptions.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          style={{
            textAlign: 'center',
            padding: '40px 0',
            color: '#94A3B8',
          }}
        >
          <AlertCircle size={40} style={{ opacity: 0.2, marginBottom: 12 }} />
          <p>All cities operating within normal parameters</p>
        </motion.div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="initial"
          animate="animate"
          style={{ display: 'flex', flexDirection: 'column', gap: 12 }}
        >
          {disruptions.map((d, i) => {
            const config = getSeverityConfig(d.severity)
            return (
              <motion.div
                key={i}
                variants={itemVariants}
                whileHover={{ x: 8, scale: 1.02 }}
                style={{
                  padding: 16,
                  borderRadius: 12,
                  background: config.bg,
                  border: `2px solid ${config.bgLight}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  cursor: 'pointer',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                {/* Animated background pulse */}
                <motion.div
                  animate={{ opacity: [0.2, 0.4, 0.2] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: config.pulse,
                    opacity: 0.1,
                  }}
                />

                {/* Icon container with glow */}
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    background: config.bgLight,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                    zIndex: 1,
                    boxShadow: `0 0 20px ${config.pulse}60`,
                  }}
                >
                  <Zap size={22} color={config.color} />
                </motion.div>

                {/* Content */}
                <div style={{ flex: 1, position: 'relative', zIndex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#1E293B' }}>
                    {d.city} • {d.type}
                  </div>
                  <div style={{ fontSize: 12, color: '#64748B', marginTop: 2 }}>
                    Severity: <span style={{ fontWeight: 700, color: config.color, textTransform: 'uppercase' }}>{d.severity}</span> • DSS Impact: {(d.dss * 100).toFixed(0)}%
                  </div>
                </div>

                {/* DSS Multiplier Badge */}
                <motion.div
                  whileHover={{ scale: 1.15 }}
                  style={{
                    textAlign: 'right',
                    position: 'relative',
                    zIndex: 1,
                  }}
                >
                  <div style={{ fontSize: 16, fontWeight: 800, color: config.color }}>
                    x{d.dss.toFixed(2)}
                  </div>
                  <div style={{ fontSize: 10, fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
                    Multiplier
                  </div>
                </motion.div>

                {/* Progress bar for DSS */}
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${d.dss * 50}%` }}
                  transition={{ duration: 1, delay: 0.3 }}
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    height: 3,
                    background: `linear-gradient(90deg, ${config.pulse}, transparent)`,
                  }}
                />
              </motion.div>
            )
          })}
        </motion.div>
      )}
    </div>
  )
}
