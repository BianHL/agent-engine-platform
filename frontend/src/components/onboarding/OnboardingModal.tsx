'use client';
import React, { useEffect } from 'react';
import { Button, Typography } from 'antd';
import { RocketOutlined, ThunderboltOutlined, SafetyOutlined } from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';

const { Title, Text } = Typography;

interface OnboardingModalProps {
  onStart: () => void;
  onSkip: () => void;
}

const features = [
  {
    icon: <RocketOutlined style={{ fontSize: 24, color: '#1890ff' }} />,
    title: 'AI Agents',
    desc: 'Build intelligent agents powered by LLMs',
  },
  {
    icon: <ThunderboltOutlined style={{ fontSize: 24, color: '#faad14' }} />,
    title: 'Workflows',
    desc: 'Automate complex multi-step processes',
  },
  {
    icon: <SafetyOutlined style={{ fontSize: 24, color: '#52c41a' }} />,
    title: 'Knowledge Base',
    desc: 'Ground agents with your domain data',
  },
];

export default function OnboardingModal({ onStart, onSkip }: OnboardingModalProps) {
  // Keyboard: Enter to start, Esc to skip
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        onStart();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onSkip();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onStart, onSkip]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 10000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(0,0,0,0.5)',
          backdropFilter: 'blur(4px)',
          padding: 16,
        }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          style={{
            background: '#fff',
            borderRadius: 16,
            boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
            width: '100%',
            maxWidth: 480,
            overflow: 'hidden',
          }}
        >
          {/* Header gradient banner */}
          <div style={{
            background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
            padding: '40px 32px 32px',
            textAlign: 'center',
          }}>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.15, type: 'spring', stiffness: 200, damping: 15 }}
              style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.2)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 16,
              }}
            >
              <RocketOutlined style={{ fontSize: 32, color: '#fff' }} />
            </motion.div>
            <Title level={3} style={{ color: '#fff', margin: 0 }}>
              Welcome to Agent Engine
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 15 }}>
              Let us show you around the platform
            </Text>
          </div>

          {/* Feature cards */}
          <div style={{ padding: '24px 32px 16px' }}>
            <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
              {features.map((f, i) => (
                <motion.div
                  key={f.title}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + i * 0.08 }}
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    padding: '16px 8px',
                    background: '#fafafa',
                    borderRadius: 10,
                    border: '1px solid #f0f0f0',
                  }}
                >
                  <div style={{ marginBottom: 8 }}>{f.icon}</div>
                  <Text strong style={{ display: 'block', fontSize: 13, marginBottom: 4 }}>
                    {f.title}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>{f.desc}</Text>
                </motion.div>
              ))}
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: 12 }}>
              <Button
                size="large"
                block
                onClick={onSkip}
              >
                Skip Tour
              </Button>
              <Button
                type="primary"
                size="large"
                block
                onClick={onStart}
                icon={<RocketOutlined />}
              >
                Start Tour
              </Button>
            </div>

            {/* Keyboard hint */}
            <div style={{ textAlign: 'center', marginTop: 12 }}>
              <Text type="secondary" style={{ fontSize: 11 }}>
                Press Enter to start, Esc to skip
              </Text>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
