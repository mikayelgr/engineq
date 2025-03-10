import { sql } from "@/src/lib/sql";
import { NextRequest, NextResponse } from "next/server";

async function getSid(lck: string) {
  const results = await sql`select id from subscribers where license = ${lck}`;
  return results[0].id;
}

async function getPid(sid: string) {
  const results =
    await sql`select * from playlists where sid = ${sid} and created_at = CURRENT_DATE`;
  return results[0].id;
}

export async function GET(request: NextRequest) {
  const lck = request.cookies.get("lck")?.value!;
  const sid = await getSid(lck);

  const tid = request.nextUrl.searchParams.get("tid");
  const pid = await getPid(sid);

  // Check if a record for this sid already exists
  const existingRecord = await sql`
    SELECT * FROM playback WHERE sid = ${sid}
  `;

  if (existingRecord.length > 0) {
    // Update existing record
    await sql`
      UPDATE playback
      SET last_tid = ${tid}, last_pid = ${pid}
      WHERE sid = ${sid}
    `;
  } else {
    // Insert new record
    await sql`
      INSERT INTO playback (sid, last_tid, last_pid)
      VALUES (${sid}, ${tid}, ${pid})
    `;
  }

  await sql`UPDATE suggestions
  SET consumed = true
  WHERE tid = ${tid}`;

  return NextResponse.json(null, { status: 200 });
}
