"use client";

import { Button, Navbar, NavbarBrand, NavbarContent } from "@heroui/react";
import { Disc, LogOut } from "lucide-react";
import Link from "next/link";

interface NavigationProps {
  actions: {
    signout: () => void;
  };
}

export default function Navigation({ actions }: NavigationProps) {
  return (
    <Navbar className="bg-gray-400 max-w-xl bg-opacity-20 my-4 mx rounded-full">
      <NavbarBrand>
        <Link
          className="flex hover:brightness-75 duration-100 ease-in-out items-center"
          href={"/dashboard"}
        >
          <Disc size={32} />
          <p className="font-semibold px-2 text-inherit">EngineQ</p>
        </Link>
      </NavbarBrand>
      <NavbarContent justify="end">
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
