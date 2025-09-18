import React, { createContext, useContext } from 'react';

export interface FeatureFlags {
  UI_ENABLE_ACTIONS_PANEL: boolean;
  UI_ENABLE_PSYOPS: boolean;
  UI_ENABLE_BLACKOPS: boolean;
}

const FlagsContext = createContext<FeatureFlags | undefined>(undefined);

export const FeatureFlagsProvider: React.FC<{ flags: FeatureFlags; children: React.ReactNode }> = ({ flags, children }) => {
  return <FlagsContext.Provider value={flags}>{children}</FlagsContext.Provider>;
};

export function useFeatureFlags(): FeatureFlags {
  const ctx = useContext(FlagsContext);
  if (!ctx) throw new Error('FeatureFlagsProvider missing');
  return ctx;
}

// Utility to build flags from Vite env (import.meta.env)
export function buildFeatureFlags(): FeatureFlags {
  const env = import.meta.env as Record<string, string | undefined>;
  const truthy = (v: string | undefined): boolean => !!v && ['1','true','on','yes','enable','enabled'].includes(v.toLowerCase());
  const isProd = env.MODE === 'production' || env.PROD === 'true';
  return {
    UI_ENABLE_ACTIONS_PANEL: truthy(env.VITE_UI_ENABLE_ACTIONS_PANEL) || true,
    UI_ENABLE_PSYOPS: truthy(env.VITE_UI_ENABLE_PSYOPS) || !isProd,
    UI_ENABLE_BLACKOPS: truthy(env.VITE_UI_ENABLE_BLACKOPS) || !isProd,
  };
}
