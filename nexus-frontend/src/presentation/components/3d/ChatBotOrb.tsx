"use client";

import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { RoundedBox, Cylinder, Sphere, Float } from "@react-three/drei";
import * as THREE from "three";

function BotHead3D() {
  const botRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (botRef.current) {
      // Gentle floating/looking animation
      botRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
      botRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
    }
  });

  return (
    <Float speed={2} rotationIntensity={0.2} floatIntensity={0.5}>
      <group ref={botRef}>
        {/* Main Head (Purple to match the Send button gradient) */}
        <RoundedBox args={[1.2, 1.2, 1.2]} radius={0.2} smoothness={4}>
          <meshPhysicalMaterial 
            color="#ffffff" // White
            metalness={0.8} 
            roughness={0.2} 
            clearcoat={1}
            emissive="#cbd5e1"
            emissiveIntensity={0.3}
          />
        </RoundedBox>

        {/* Face Screen (Dark) */}
        <RoundedBox args={[1.0, 0.6, 1.25]} radius={0.1} smoothness={4} position={[0, 0, 0.05]}>
          <meshBasicMaterial color="#05050a" />
        </RoundedBox>

        {/* Left Eye (Cyan) */}
        <Sphere args={[0.15, 16, 16]} position={[-0.25, 0, 0.65]}>
          <meshBasicMaterial color="#06b6d4" />
        </Sphere>
        
        {/* Right Eye (Cyan) */}
        <Sphere args={[0.15, 16, 16]} position={[0.25, 0, 0.65]}>
          <meshBasicMaterial color="#06b6d4" />
        </Sphere>

        {/* Antenna Base */}
        <Cylinder args={[0.05, 0.05, 0.4]} position={[0, 0.7, 0]}>
          <meshStandardMaterial color="#ffffff" metalness={0.7} roughness={0.2} />
        </Cylinder>

        {/* Antenna Tip (Cyan) */}
        <Sphere args={[0.1, 16, 16]} position={[0, 0.9, 0]}>
          <meshBasicMaterial color="#06b6d4" />
        </Sphere>

        {/* Internal lights for the eyes */}
        <pointLight position={[-0.25, 0, 0.8]} color="#06b6d4" intensity={2} distance={2} />
        <pointLight position={[0.25, 0, 0.8]} color="#06b6d4" intensity={2} distance={2} />
        
        {/* Antenna Light */}
        <pointLight position={[0, 1, 0]} color="#06b6d4" intensity={1} distance={2} />
      </group>
      
      {/* Studio Lighting mapped to Purple and Cyan */}
      <ambientLight intensity={1.5} />
      {/* White light */}
      <directionalLight position={[-5, -5, 5]} intensity={2.5} color="#ffffff" />
      {/* Cyan light */}
      <directionalLight position={[5, 5, 5]} intensity={2.5} color="#06b6d4" />
    </Float>
  );
}

export default function ChatBotOrb() {
  return (
    <div className="absolute inset-0 z-0 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 4.5], fov: 45 }} className="w-full h-full">
        <BotHead3D />
      </Canvas>
    </div>
  );
}


