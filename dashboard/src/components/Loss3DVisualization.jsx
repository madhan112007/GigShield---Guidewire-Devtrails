import React, { useRef, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, PerspectiveCamera } from '@react-three/drei'
import * as THREE from 'three'
import { motion } from 'framer-motion'

function Bar3D({ position, height, color, label, value }) {
  const meshRef = useRef()
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.002
      meshRef.current.position.y = Math.sin(state.clock.elapsedTime) * 0.2
    }
  })

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        position={[0, height / 2, 0]}
        castShadow
        receiveShadow
      >
        <boxGeometry args={[0.6, height, 0.6]} />
        <meshStandardMaterial 
          color={color}
          metalness={0.6}
          roughness={0.3}
          emissive={color}
          emissiveIntensity={0.2}
        />
      </mesh>
      <Text
        position={[0, height + 0.5, 0]}
        fontSize={0.3}
        color="#fff"
        anchorX="center"
        anchorY="bottom"
      >
        {value.toFixed(1)}%
      </Text>
      <Text
        position={[0, -0.5, 0]}
        fontSize={0.25}
        color="#666"
        anchorX="center"
        anchorY="top"
      >
        {label}
      </Text>
    </group>
  )
}

function Scene3DLossRatios({ data }) {
  const controlsRef = useRef()

  const colors = ['#1A56DB', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4', '#EC4899', '#14B8A6']
  
  const spacing = 2.5
  const startX = -(data.length - 1) * spacing / 2

  return (
    <Canvas shadows camera={{ position: [0, 3, 8], fov: 50 }}>
      <PerspectiveCamera makeDefault position={[0, 3, 8]} fov={50} />
      <OrbitControls ref={controlsRef} autoRotate autoRotateSpeed={2} enableZoom enablePan />
      
      <ambientLight intensity={0.8} />
      <directionalLight
        position={[5, 10, 5]}
        intensity={1}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <pointLight position={[-5, 5, 5]} intensity={0.5} />
      
      {data.map((item, idx) => (
        <Bar3D
          key={idx}
          position={[startX + idx * spacing, 0, 0]}
          height={Math.max(item.loss_ratio, 0.1) * 3}
          color={colors[idx % colors.length]}
          label={item.city}
          value={item.loss_ratio * 100}
        />
      ))}

      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[20, 20]} />
        <shadowMaterial opacity={0.3} />
      </mesh>
      
      <gridHelper args={[20, 20]} />
    </Canvas>
  )
}

export function Loss3DVisualization({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div style={{ width: '100%', height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ccc' }}>
        No loss ratio data available
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6 }}
      style={{ width: '100%', height: '100%', minHeight: 400 }}
    >
      <Scene3DLossRatios data={data} />
    </motion.div>
  )
}
