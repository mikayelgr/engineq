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
          <p className="font-semibold px-2 text-inherit">EngineQ</p>
        </Link>
      </NavbarBrand>
      <NavbarContent justify="end" className="gap-4">
        <NavbarItem>
          <div className="flex items-center text-gray-500 text-xs">
            <Phone size={12} className="mr-1" />
            <span>Support: +374 33 999 461</span>
          </div>
        </NavbarItem>
        <Button
          size="sm"
          onPress={() => actions.signout()}
          startContent={<LogOut size={14} />}
          variant="flat"
          color="default"
        >
          Sign Out
        </Button>
      </NavbarContent>
    </Navbar>
  );
}
