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
