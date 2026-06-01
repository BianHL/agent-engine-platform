'use client';
import React, { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import OnboardingModal from './OnboardingModal';
import OnboardingTooltip from './OnboardingTooltip';
import ProgressIndicator from './ProgressIndicator';

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  targetSelector: string;
  route: string;
  icon: React.ReactNode;
}

interface OnboardingContextValue {
  isActive: boolean;
  currentStep: number;
  totalSteps: number;
  steps: OnboardingStep[];
  startOnboarding: () => void;
  nextStep: () => void;
  prevStep: () => void;
  skipOnboarding: () => void;
  completeOnboarding: () => void;
  isCompleted: boolean;
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

export function useOnboarding() {
  const ctx = useContext(OnboardingContext);
  if (!ctx) throw new Error('useOnboarding must be used within OnboardingProvider');
  return ctx;
}

const STORAGE_KEY = 'onboarding_completed';

function isOnboardingCompleted(): boolean {
  if (typeof window === 'undefined') return true;
  return localStorage.getItem(STORAGE_KEY) === 'true';
}

function markCompleted() {
  localStorage.setItem(STORAGE_KEY, 'true');
}

interface OnboardingProviderProps {
  children: ReactNode;
  steps: OnboardingStep[];
}

export default function OnboardingProvider({ children, steps }: OnboardingProviderProps) {
  const router = useRouter();
  const [showModal, setShowModal] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isCompleted, setIsCompleted] = useState(true);

  useEffect(() => {
    const completed = isOnboardingCompleted();
    setIsCompleted(completed);
    if (!completed) {
      setShowModal(true);
    }
  }, []);

  const startOnboarding = useCallback(() => {
    setShowModal(false);
    setIsActive(true);
    setCurrentStep(0);
    if (steps[0]?.route) {
      router.push(steps[0].route);
    }
  }, [steps, router]);

  const nextStep = useCallback(() => {
    if (currentStep < steps.length - 1) {
      const next = currentStep + 1;
      setCurrentStep(next);
      if (steps[next]?.route) {
        router.push(steps[next].route);
      }
    } else {
      markCompleted();
      setIsCompleted(true);
      setIsActive(false);
    }
  }, [currentStep, steps, router]);

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      const prev = currentStep - 1;
      setCurrentStep(prev);
      if (steps[prev]?.route) {
        router.push(steps[prev].route);
      }
    }
  }, [currentStep, steps, router]);

  const skipOnboarding = useCallback(() => {
    markCompleted();
    setIsCompleted(true);
    setIsActive(false);
    setShowModal(false);
  }, []);

  const completeOnboarding = useCallback(() => {
    markCompleted();
    setIsCompleted(true);
    setIsActive(false);
  }, []);

  const ctx: OnboardingContextValue = {
    isActive,
    currentStep,
    totalSteps: steps.length,
    steps,
    startOnboarding,
    nextStep,
    prevStep,
    skipOnboarding,
    completeOnboarding,
    isCompleted,
  };

  return (
    <OnboardingContext.Provider value={ctx}>
      {children}
      {showModal && !isCompleted && (
        <OnboardingModal onStart={startOnboarding} onSkip={skipOnboarding} />
      )}
      {isActive && (
        <>
          <OnboardingTooltip
            step={steps[currentStep]}
            stepIndex={currentStep}
            totalSteps={steps.length}
            onNext={nextStep}
            onPrev={prevStep}
            onSkip={skipOnboarding}
          />
          <ProgressIndicator
            current={currentStep}
            total={steps.length}
          />
        </>
      )}
    </OnboardingContext.Provider>
  );
}
