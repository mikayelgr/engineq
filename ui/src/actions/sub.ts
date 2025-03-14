"use server";

import { cookies } from "next/headers";
import { sql } from "../lib/sql";

export async function getPrompts() {
  const c = await cookies();
  const lck = c.get("lck")!;
  const qr = await sql`
    SELECT * FROM prompts p
    LEFT JOIN subscribers s on p.sid = s.id
    WHERE s.license = ${lck.value}
    LIMIT 1; 
  `;

  return qr[0];
}
