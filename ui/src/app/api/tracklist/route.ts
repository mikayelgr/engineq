import { NextRequest, NextResponse } from "next/server";
import amqplib from "amqplib";
import { sql } from "@/src/lib/sql";

let mq: amqplib.ChannelModel | null = null;
let ch: amqplib.Channel | null = null;

async function getRemainingSuggestionsCount(lck: string) {
  // Get subscriber ID, today's playlist, and playback info in a single query
  const userInfo = await sql`
    SELECT 
      sub.id as sid, 
      plist.id as today_pid,
      pb.suggestion_id as last_suggestion_id
    FROM subscribers sub
    LEFT JOIN playback pb ON pb.subscriber_id = sub.id
    LEFT JOIN playlists plist ON plist.sid = sub.id AND plist.created_at = CURRENT_DATE
    WHERE sub.license = ${lck}`;

  // If no playlist exists for today, return 0
  if (!userInfo[0]?.today_pid) {
    return 0;
  }

  const todayPid = userInfo[0].today_pid;
  const lastSuggestionId = userInfo[0].last_suggestion_id;

  // If continuing the same playlist, count suggestions added after the last suggestion
  if (lastSuggestionId) {
    const result = await sql`
      WITH last_position AS (
        SELECT added_at
        FROM suggestions
        WHERE id = ${lastSuggestionId}
        LIMIT 1 -- Ensure only one row is returned
      )
      SELECT COUNT(*) as count
      FROM suggestions s
      WHERE s.pid = ${todayPid}
      AND s.added_at > (SELECT added_at FROM last_position)`;

    return parseInt(result[0]?.count || "0", 10);
  } else {
    // If this is a new playlist or no previous suggestion exists, return all suggestions for the playlist
    const result = await sql`
      SELECT COUNT(*) as count 
      FROM suggestions 
      WHERE pid = ${todayPid}`;
    return parseInt(result[0]?.count || "0", 10);
  }
}

export async function GET(request: NextRequest) {
  if (!mq) mq = await amqplib.connect(process.env.AMQP_URL!);
  if (!ch) {
    ch = await mq.createChannel();
    await ch.assertQueue("acura");
  }

  const lck = request.cookies.get("lck")!.value;
  const queue = (
    await sql`
SELECT
  trk.id,
  trk.title,
  trk.artist,
  trk.duration,
  trk.image,
  trk.uri,
  sug.added_at,
  sug.id as suggestion_id 
FROM playlists plist
JOIN subscribers sub ON sub.id = plist.sid AND sub.license = ${lck}
JOIN suggestions sug ON sug.pid = plist.id
JOIN tracks trk ON sug.tid = trk.id
LEFT JOIN playback plb ON plb.subscriber_id = sub.id
WHERE plist.created_at = CURRENT_DATE
  AND (
    plb.suggestion_id IS NULL
    OR sug.id NOT IN (
      SELECT suggestion_id FROM playback 
      WHERE subscriber_id = sub.id AND suggestion_id IS NOT NULL
    )
  )
ORDER BY sug.added_at ASC;
  `
  ).flatMap((t) => t);

  const countOfSuggestions = await getRemainingSuggestionsCount(lck);
  if (countOfSuggestions <= 10) {
    ch.sendToQueue(
      "acura",
      Buffer.from(
        JSON.stringify({ license: request.cookies.get("lck")?.value })
      )
    );
  }

  return NextResponse.json(queue, { status: 200 });
}
