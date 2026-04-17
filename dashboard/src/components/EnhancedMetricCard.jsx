import React from 'react'
import { motion } from 'framer-motion'
import { AnimatedCounter } from './AnimatedCounter'

export function EnhancedMetricCard({
  Icon,
  label,
  value,
  trend,
  color,
  isCurrency,
  gradient = false,
  delay = 0,
}) {
  const isPositive = trend > 0

  const containerVariants = {
    initial: { opacity: 0, y: 20 },
    animate: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, delay },
    },
    hover: {
      y: -8,
      boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
    },
  }

  const iconVariants = {
    initial: { scale: 0, rotate: -180 },
    animate: { scale: 1, rotate: 0, transition: { duration: 0.6, delay: delay + 0.1 } },
    hover: { scale: 1.15, rotate: 10 },
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      style={{
        background: gradient
          ? `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`
          : '#ffffff',
        border: `1px solid ${color}30`,
        borderRadius: 16,
        padding: 24,
        position: 'relative',
        overflow: 'hidden',
        cursor: 'pointer',
      }}
    >
      {/* Animated background blob */}
      <motion.div
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 0.1, scale: 1 }}
        transition={{ duration: 0.8, delay }}
        style={{
          position: 'absolute',
          top: -50,
          right: -50,
          width: 200,
          height: 200,
          borderRadius: '50%',
          background: color,
          filter: 'blur(60px)',
        }}
      />

      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <motion.div
            variants={iconVariants}
            initial="initial"
            animate="animate"
            whileHover="hover"
            style={{
              width: 50,
              height: 50,
              borderRadius: 12,
              background: `${color}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Icon size={24} color={color} />
          </motion.div>

          {trend !== undefined && (
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: delay + 0.2 }}
              style={{
                fontSize: 12,
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                color: isPositive ? '#10B981' : '#EF4444',
                background: isPositive ? '#ECFDF5' : '#FEF2F2',
                padding: '6px 12px',
                borderRadius: 20,
              }}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ transform: isPositive ? 'none' : 'rotate(180deg)' }}>
                <path
                  d="M7 2L12.5 9H1.5L7 2Z"
                  fill="currentColor"
                />
              </svg>
              {Math.abs(trend)}%
            </motion.div>
          )}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: delay + 0.3 }}
        >
          <div style={{ fontSize: 12, fontWeight: 600, color: '#64748B', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {label}
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: '#1E293B', letterSpacing: '-1px' }}>
            <AnimatedCounter
              value={value}
              duration={1.5}
              isCurrency={isCurrency}
              prefix={isCurrency ? '' : ''}
            />
          </div>
        </motion.div>

        {/* Bottom accent bar */}
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: '100%' }}
          transition={{ duration: 0.8, delay: delay + 0.4 }}
          style={{
            height: 3,
            background: `linear-gradient(90deg, ${color}, transparent)`,
            borderRadius: 2,
            marginTop: 12,
          }}
        />
      </div>
    </motion.div>
  )
}
