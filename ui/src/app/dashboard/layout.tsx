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
