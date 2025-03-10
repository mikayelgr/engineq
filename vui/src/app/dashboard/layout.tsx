import { ScrollShadow } from "@heroui/react";
import Navigation from "@/src/components/navigation";
import { signout } from "@/src/actions/auth";
import { DashboardStoreProvider } from "@/src/providers/dashboard/dashboard-store-provider";

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="w-full shadow-none flex items-center justify-center flex-col h-screen">
      <DashboardStoreProvider>
        <Navigation actions={{ signout }} />

        {/* Content area */}
        <div className="flex-1 w-full overflow-hidden max-h-[35rem]">
          {/* This wrapper ensures the content below navbar is scrollable */}
          <div className="h-full w-full overflow-y-auto">
            <ScrollShadow className="w-full h-full">{children}</ScrollShadow>
          </div>
        </div>
      </DashboardStoreProvider>
    </div>
  );
}
