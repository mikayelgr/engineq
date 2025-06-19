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

import {
  Button,
  Navbar,
  NavbarBrand,
  NavbarContent,
  NavbarItem,
} from "@heroui/react";
import { Disc, LogOut, Phone } from "lucide-react";
import Link from "next/link";

interface NavigationProps {
  actions: {
    signout: () => void;
  };
}

export default function Navigation({ actions }: NavigationProps) {
  return (
    <Navbar className="bg-gray-400 w-full max-w-xl bg-opacity-20 mx rounded-full">
      <NavbarBrand>
        <Link
          className="flex hover:brightness-75 duration-100 ease-in-out items-center"
          href={"/dashboard"}
        >
          <Disc size={32} />
          <p className="font-semibold px-2 text-inherit hidden sm:inline">
            EngineQ
          </p>
        </Link>
      </NavbarBrand>
      <NavbarContent justify="end" className="gap-2 sm:gap-4">
        {/* Phone display for xs screens and up */}
        <NavbarItem className="hidden md:block">
          <Link
            href={"tel:+37433999461"}
            className="flex items-center text-gray-500 text-xs"
          >
            <Phone size={12} className="mr-1" />
            <span className="hidden md:inline">Support: +374 33 999 461</span>
            <span className="inline md:hidden">+374 33 999 461</span>
          </Link>
        </NavbarItem>
        {/* Phone icon only for smallest screens */}
        <NavbarItem className="md:hidden">
          <Link href="tel:+37433999461" className="text-gray-500">
            <Phone size={16} />
          </Link>
        </NavbarItem>
        <Button
          size="sm"
          onPress={() => actions.signout()}
          startContent={<LogOut size={14} />}
          variant="flat"
          color="danger"
          className="min-w-0 px-2 xs:min-w-[60px] sm:px-3"
        >
          <span className="hidden xs:inline sm:hidden">Exit</span>
          <span className="hidden sm:inline">Sign Out</span>
        </Button>
      </NavbarContent>
    </Navbar>
  );
}
