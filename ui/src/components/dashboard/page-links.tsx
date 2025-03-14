"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function DashboardPageLinks() {
  const pathname = usePathname();
  return (
    <>
      <Link
        className={clsx(
          pathname === "/dashboard" && "decoration-wavy underline font-bold"
        )}
        href={"/dashboard"}
      >
        Dashboard
      </Link>
      <Link
        className={clsx(
          pathname === "/dashboard/settings" &&
            "decoration-wavy underline font-bold"
        )}
        href={"/dashboard/settings"}
      >
        Settings
      </Link>
    </>
  );
}
