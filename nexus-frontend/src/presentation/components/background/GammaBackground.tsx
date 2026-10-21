'use client';

import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function Particles({ count, color }: { count: number; color: string }) {
  const mesh = useRef<THREE.Points>(null);
  
  const particles = useMemo(() => {
    const temp = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos((Math.random() * 2) - 1);
      const r = 10 + Math.random() * 20; // Sphere radius between 10 and 30

      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);

      temp[i * 3] = x;
      temp[i * 3 + 1] = y;
      temp[i * 3 + 2] = z;
    }
    return temp;
  }, [count]);

  useFrame((state) => {
    if (mesh.current) {
      mesh.current.rotation.x = state.clock.getElapsedTime() * 0.05;
      mesh.current.rotation.y = state.clock.getElapsedTime() * 0.07;
    }
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[particles, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.15}
        color={color}
        transparent
        opacity={0.6}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

function Starfield() {
  const mesh = useRef<THREE.Points>(null);
  const count = 2000;
  
  const particles = useMemo(() => {
    const temp = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      temp[i * 3] = (Math.random() - 0.5) * 100;
      temp[i * 3 + 1] = (Math.random() - 0.5) * 100;
      temp[i * 3 + 2] = (Math.random() - 0.5) * 100;
    }
    return temp;
  }, [count]);

  useFrame((state) => {
    if (mesh.current) {
      mesh.current.rotation.y = state.clock.getElapsedTime() * 0.02;
    }
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[particles, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color="#ffffff"
        transparent
        opacity={0.3}
        sizeAttenuation
      />
    </points>
  );
}

export function GammaBackground() {
  return (
    <div className="fixed inset-0 -z-10 bg-[#070914]">
      <Canvas camera={{ position: [0, 0, 35], fov: 60 }}>
        <fog attach="fog" args={['#070914', 20, 50]} />
        <Starfield />
        {/* Electric Cyan Sphere */}
        <group position={[-5, 0, 0]}>
          <Particles count={3000} color="#00e5ff" />
        </group>
        {/* Fiery Orange Sphere */}
        <group position={[5, 0, 0]}>
          <Particles count={3000} color="#ff5500" />
        </group>
      </Canvas>
    </div>
  );
}
