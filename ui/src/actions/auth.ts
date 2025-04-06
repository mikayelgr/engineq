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
