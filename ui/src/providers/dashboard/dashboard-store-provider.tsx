// src/providers/counter-store-provider.tsx
"use client";

import { type ReactNode, createContext, useRef, useContext } from "react";
import { useStore } from "zustand";

import {
  type DashboardStore,
  createDashboardStore,
} from "@/src/stores/dashboard/dashboard-store";

export type DashboardStoreApi = ReturnType<typeof createDashboardStore>;

export const DashboardStoreContext = createContext<
  DashboardStoreApi | undefined
>(undefined);

export interface DashboardStoreProviderProps {
  children: ReactNode;
}

export const DashboardStoreProvider = ({
  children,
}: DashboardStoreProviderProps) => {
  const storeRef = useRef<DashboardStoreApi | null>(null);
  if (!storeRef.current) {
    storeRef.current = createDashboardStore();
  }

  return (
    <DashboardStoreContext.Provider value={storeRef.current}>
      {children}
    </DashboardStoreContext.Provider>
  );
};

export const useDashboardStore = <T,>(
  selector: (store: DashboardStore) => T
): T => {
  const ctx = useContext(DashboardStoreContext);
  if (!ctx) {
    throw new Error(
      `useDashboardStore must be used within DashboardStoreProvider`
    );
  }

  return useStore(ctx, selector);
};
