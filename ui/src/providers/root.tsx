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

"use client";

import type { ThemeProviderProps } from "next-themes";

import * as React from "react";
import { HeroUIProvider } from "@heroui/system";
import { useRouter } from "next/navigation";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "@heroui/react";

export interface ProvidersProps {
  children: React.ReactNode;
  themeProps?: ThemeProviderProps;
}

declare module "@react-types/shared" {
  interface RouterConfig {
    routerOptions: NonNullable<
      Parameters<ReturnType<typeof useRouter>["push"]>[1]
    >;
  }
}

const queryClient = new QueryClient();

export function Providers({ children, themeProps }: ProvidersProps) {
  const router = useRouter();

  return (
    <HeroUIProvider navigate={router.push}>
      <QueryClientProvider client={queryClient}>
        <ToastProvider placement="bottom-center" />
        {children}
      </QueryClientProvider>
    </HeroUIProvider>
  );
}
