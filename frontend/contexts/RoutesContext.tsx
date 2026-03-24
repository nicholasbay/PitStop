'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

import { RouteResult, RoutesContextType } from '@/types';

export const RoutesContext = createContext<RoutesContextType | undefined>(undefined);

export function RoutesProvider({ children }: { children: ReactNode }) {
  const [routes, setRoutes] = useState<RouteResult[]>([]);
  const [currentRoute, setCurrentRoute] = useState<RouteResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const clearRoutes = () => {
    setRoutes([]);
    setCurrentRoute(null);
  };

  const value: RoutesContextType = {
    routes,
    currentRoute,
    loading,
    error,
    setRoutes,
    setCurrentRoute,
    setLoading,
    setError,
    clearRoutes,
  };

  return (
    <RoutesContext.Provider value={value}>
      {children}
    </RoutesContext.Provider>
  );
}

export function useRoutes() {
  const context = useContext(RoutesContext);
  if (context === undefined) {
    throw new Error('useRoutes must be used within a RoutesProvider');
  }
  return context;
}