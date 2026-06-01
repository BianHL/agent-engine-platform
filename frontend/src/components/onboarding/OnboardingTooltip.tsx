'use client';
import React, { useEffect, useState, useRef } from 'react';
import { Button, Typography } from 'antd';
import { ArrowLeftOutlined, ArrowRightOutlined, CloseOutlined } from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import type { OnboardingStep } from './OnboardingProvider';

const { Text } = Typography;

interface Position {
  top: number;
  left: number;
  placement: 'bottom' | 'top' | 'right' | 'left';
  arrowOffset: number;
}

interface OnboardingTooltipProps {
  step: OnboardingStep;
  stepIndex: number;
  totalSteps: number;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
}

export default function OnboardingTooltip({
  step,
  stepIndex,
  totalSteps,
  onNext,
  onPrev,
  onSkip,
}: OnboardingTooltipProps) {
  const [position, setPosition] = useState<Position | null>(null);
  const [highlightRect, setHighlightRect] = useState<DOMRect | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updatePosition = () => {
      const el = document.querySelector(step.targetSelector);
      if (!el || !tooltipRef.current) {
        setPosition(null);
        setHighlightRect(null);
        return;
      }

      const rect = el.getBoundingClientRect();
      const tooltipEl = tooltipRef.current;
      const tooltipRect = tooltipEl.getBoundingClientRect();
      const padding = 12;
      const offset = 16;

      setHighlightRect(rect);

      let placement: Position['placement'] = 'bottom';
      let top = rect.bottom + offset;
      let left = rect.left + rect.width / 2 - tooltipRect.width / 2;

      // Prefer bottom, but flip to top if not enough space
      if (top + tooltipRect.height > window.innerHeight - padding) {
        placement = 'top';
        top = rect.top - tooltipRect.height - offset;
      }
      // If top overflows, try right
      if (top < padding) {
        placement = 'right';
        top = rect.top + rect.height / 2 - tooltipRect.height / 2;
        left = rect.right + offset;
      }
      // If right overflows, try left
      if (left + tooltipRect.width > window.innerWidth - padding) {
        placement = 'left';
        left = rect.left - tooltipRect.width - offset;
      }

      // Clamp horizontal
      left = Math.max(padding, Math.min(left, window.innerWidth - tooltipRect.width - padding));
      // Clamp vertical
      top = Math.max(padding, Math.min(top, window.innerHeight - tooltipRect.height - padding));

      const arrowOffset = rect.left + rect.width / 2 - left;

      setPosition({ top, left, placement, arrowOffset });
    };

    // Small delay to allow DOM to settle after route change
    const timer = setTimeout(updatePosition, 300);
    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition, true);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition, true);
    };
  }, [step.targetSelector]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        onNext();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onSkip();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        onPrev();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        onNext();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onNext, onPrev, onSkip]);

  // Scroll target into view
  useEffect(() => {
    const el = document.querySelector(step.targetSelector);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [step.targetSelector]);

  const isFirst = stepIndex === 0;
  const isLast = stepIndex === totalSteps - 1;

  return (
    <>
      {/* Overlay with cutout highlight */}
      <AnimatePresence>
        {highlightRect && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 9998,
              pointerEvents: 'none',
            }}
          >
            <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
              <defs>
                <mask id="onboarding-mask">
                  <rect width="100%" height="100%" fill="white" />
                  <rect
                    x={highlightRect.left - 6}
                    y={highlightRect.top - 6}
                    width={highlightRect.width + 12}
                    height={highlightRect.height + 12}
                    rx={8}
                    fill="black"
                  />
                </mask>
              </defs>
              <rect
                width="100%"
                height="100%"
                fill="rgba(0,0,0,0.5)"
                mask="url(#onboarding-mask)"
              />
              {/* Animated border around target */}
              <rect
                x={highlightRect.left - 6}
                y={highlightRect.top - 6}
                width={highlightRect.width + 12}
                height={highlightRect.height + 12}
                rx={8}
                fill="none"
                stroke="#1890ff"
                strokeWidth={2}
                strokeDasharray="8 4"
                style={{ animation: 'onboarding-pulse 2s ease-in-out infinite' }}
              />
            </svg>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tooltip */}
      <AnimatePresence mode="wait">
        {position && (
          <motion.div
            ref={tooltipRef}
            key={step.id}
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            style={{
              position: 'fixed',
              top: position.top,
              left: position.left,
              zIndex: 9999,
              width: 340,
              maxWidth: 'calc(100vw - 32px)',
            }}
          >
            <div
              style={{
                background: '#fff',
                borderRadius: 12,
                boxShadow: '0 12px 40px rgba(0,0,0,0.15), 0 4px 12px rgba(0,0,0,0.1)',
                padding: '20px 20px 16px',
                position: 'relative',
              }}
            >
              {/* Arrow */}
              {(position.placement === 'top' || position.placement === 'bottom') && (
                <div
                  style={{
                    position: 'absolute',
                    [position.placement === 'bottom' ? 'top' : 'bottom']: -6,
                    left: Math.max(16, Math.min(position.arrowOffset, 340 - 16)),
                    transform: 'translateX(-50%) rotate(45deg)',
                    width: 12,
                    height: 12,
                    background: '#fff',
                    boxShadow: position.placement === 'bottom'
                      ? '-2px -2px 4px rgba(0,0,0,0.06)'
                      : '2px 2px 4px rgba(0,0,0,0.06)',
                  }}
                />
              )}

              {/* Close button */}
              <Button
                type="text"
                size="small"
                icon={<CloseOutlined />}
                onClick={onSkip}
                style={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  color: '#999',
                  width: 28,
                  height: 28,
                }}
              />

              {/* Step indicator */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <div style={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  background: '#1890ff',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 13,
                  fontWeight: 600,
                  flexShrink: 0,
                }}>
                  {stepIndex + 1}
                </div>
                <Text strong style={{ fontSize: 16 }}>{step.title}</Text>
              </div>

              {/* Description */}
              <Text style={{ display: 'block', color: '#666', marginBottom: 16, lineHeight: 1.6 }}>
                {step.description}
              </Text>

              {/* Action buttons */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  {!isFirst && (
                    <Button
                      icon={<ArrowLeftOutlined />}
                      onClick={onPrev}
                      style={{ marginRight: 8 }}
                    >
                      Back
                    </Button>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <Button onClick={onSkip}>Skip</Button>
                  <Button
                    type="primary"
                    icon={isLast ? undefined : <ArrowRightOutlined />}
                    iconPosition="end"
                    onClick={onNext}
                  >
                    {isLast ? 'Get Started' : 'Next'}
                  </Button>
                </div>
              </div>

              {/* Keyboard hint */}
              <div style={{ marginTop: 12, textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  Press Enter to continue, Esc to skip
                </Text>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* CSS for pulse animation */}
      <style jsx global>{`
        @keyframes onboarding-pulse {
          0%, 100% { stroke-opacity: 1; }
          50% { stroke-opacity: 0.5; }
        }
      `}</style>
    </>
  );
}
