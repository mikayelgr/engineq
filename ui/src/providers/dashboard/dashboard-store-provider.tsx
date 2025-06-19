// EngineQ: An AI-enabled music management system.
// Copyright (C) 2025  Mikayel Grigoryan
// 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
// 
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
// 
// For inquiries, contact: michael.grigoryan25@gmail.com
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
