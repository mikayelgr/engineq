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

export async function getSettings() {
  const c = await cookies();
  const lck = c.get("lck")!;

  const prompts = await sql`
  SELECT p.id, p.prompt FROM prompts p
  LEFT JOIN subscribers s ON p.sid = s.id
  WHERE s.license = ${lck.value}
  `;

  return { prompts };
}

interface SetSettingsProps {
  prompts: Record<string, any>[];
}

export async function setSettings(props: SetSettingsProps) {
  const c = await cookies();
  const lck = c.get("lck")!;

  try {
    const sid = (
      await sql`SELECT id FROM subscribers WHERE license = ${lck.value}`
    )[0].id;

    for (const { id, prompt } of props.prompts) {
      // if id is less than 0, it means it's a new prompt
      if (id < 0) {
        await sql`INSERT INTO prompts (sid, prompt) VALUES (${sid}, ${prompt})`;
      } else {
        await sql`UPDATE prompts SET prompt = ${prompt} WHERE id = ${id} AND sid = ${sid}`;
      }
    }

    return {
      prompts:
        await sql`SELECT p.id, p.prompt FROM prompts p WHERE p.sid = ${sid}`,
    };
  } catch (error) {
    console.error("Error when updating settings: ", error);
    return null;
  }
}
