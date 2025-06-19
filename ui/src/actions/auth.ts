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
"use server";

import { sql } from "@/src/lib/sql";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const LICENSE_COOKIE_NAME = "lck";

export async function check() {
  const c = await cookies();
  const lck = c.get(LICENSE_COOKIE_NAME);
  if (!lck) return false;

  try {
    const subs =
      await sql`SELECT * FROM subscribers WHERE license = ${lck.value}`;
    return subs.length > 0;
  } catch (error) {
    console.error(error);
    return false;
  }
}

export async function signin(
  form: FormData
): Promise<{ error: string } | null> {
  const key = form.get("key")?.toString();
  if (!key || key.length === 0) {
    return { error: "Please provide a valid key." };
  }

  try {
    const subs = await sql`SELECT * FROM subscribers WHERE license = ${key}`;
    if (subs.length === 0) {
      return { error: "License key not found." };
    }

    const sub = subs[0];
    const c = await cookies();
    c.set(LICENSE_COOKIE_NAME, sub.license, { httpOnly: true });
  } catch (error) {
    console.error(error);
    return { error: "Please provide a valid key." };
  }

  redirect("/dashboard"); // Never put redirects in try/catch, because they work by throwing errors
}

export async function signout() {
  const c = await cookies();
  c.delete(LICENSE_COOKIE_NAME);
  redirect("/");
}
