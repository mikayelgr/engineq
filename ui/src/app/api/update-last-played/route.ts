import { sql } from "@/src/lib/sql";
import { NextRequest, NextResponse } from "next/server";

async function getSubscriberId(lck: string) {
  const results = await sql`SELECT id FROM subscribers WHERE license = ${lck}`;
  return results[0].id;
}

export async function GET(request: NextRequest) {
  const lck = request.cookies.get("lck")?.value!;
  const subscriberId = await getSubscriberId(lck);
  const suggestionId = request.nextUrl.searchParams.get("sid");

  // Check if a record for this sid already exists
  const existingRecord = await sql`
    SELECT * FROM playback WHERE subscriber_id = ${subscriberId}
  `;

  if (existingRecord.length > 0) {
    // Update existing record
    await sql`
      UPDATE playback
      SET suggestion_id = ${suggestionId}
      WHERE subscriber_id = ${subscriberId}
    `;
  } else {
    // Insert new record into the playback table, specifying the suggestion and subscriber IDs
    await sql`
      INSERT INTO playback (subscriber_id, suggestion_id)
      VALUES (${subscriberId}, ${suggestionId})
    `;
  }

  return NextResponse.json(null, { status: 200 });
}
