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
import { ScrollShadow } from "@heroui/react";
import Navigation from "@/src/components/navigation";
import { signout } from "@/src/actions/auth";
import { DashboardStoreProvider } from "@/src/providers/dashboard/dashboard-store-provider";
import DashboardPageLinks from "@/src/components/dashboard/page-links";

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="w-full shadow-none flex items-center justify-center flex-col h-screen">
      <DashboardStoreProvider>
        <div className="w-full flex flex-col gap-6">
          <div className="w-full mt-8 px-4 flex items-center justify-center">
            <Navigation actions={{ signout }} />
          </div>

          <div className="w-full flex items-center justify-center gap-4">
            <DashboardPageLinks />
          </div>
        </div>

        {/* Content area */}
        <div className="flex-1 pt-4 pb-4 w-full overflow-hidden h-full">
          {/* This wrapper ensures the content below navbar is scrollable */}
          <div className="h-full w-full overflow-y-auto">
            <ScrollShadow className="w-full h-full p-4">
              {children}
            </ScrollShadow>
          </div>
        </div>
      </DashboardStoreProvider>
    </div>
  );
}
