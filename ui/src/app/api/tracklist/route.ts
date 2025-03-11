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
      p.id as today_pid,
      pb.last_pid, 
      pb.last_tid
    FROM subscribers sub
    LEFT JOIN playback pb ON pb.sid = sub.id
    LEFT JOIN playlists p ON p.sid = sub.id AND p.created_at = CURRENT_DATE
    WHERE sub.license = ${lck}`;

  // If no playlist exists for today, return 0
  if (!userInfo[0].today_pid) {
    return 0;
  }

  const todayPid = userInfo[0].today_pid;
  const lastPid = userInfo[0].last_pid;
  const lastTid = userInfo[0].last_tid;

  // If continuing the same playlist, count suggestions added after their last track
  if (lastPid === todayPid && lastTid) {
    const result = await sql`
      WITH last_position AS (
        SELECT added_at
        FROM suggestions
        WHERE pid = ${lastPid} AND tid = ${lastTid}
      )
      SELECT COUNT(*) as count
      FROM suggestions s
      WHERE s.pid = ${todayPid}
      AND s.consumed = false
      AND (s.added_at > (SELECT added_at FROM last_position) OR NOT EXISTS (SELECT 1 FROM last_position))`;

    return parseInt(result[0].count, 10);
  } else {
    // If this is a new playlist or they haven't started yet, return all unconsumed suggestions
    const result = await sql`
      SELECT COUNT(*) as count
      FROM suggestions
      WHERE pid = ${todayPid}
      AND consumed = false`;

    return parseInt(result[0].count, 10);
  }
}

export async function GET(request: NextRequest) {
  if (!mq) mq = await amqplib.connect(process.env.AMQP_URL!);
  if (!ch) {
    ch = await mq.createChannel();
    await ch.assertQueue("acura");
  }

  const lck = request.cookies.get("lck")!.value; // we are guaranteed to have this
  const tid = Number(request.nextUrl.searchParams.get("tid")) || -1;
  if (!tid) {
    return NextResponse.json(
      {
        error:
          "Current track id (`current_tid`) and playlist id (`pid`) " +
          "must be provided as search params.",
      },
      { status: 400 }
    );
  }

  const queue = (
    await sql`
SELECT t.*, sug.added_at 
FROM playlists p
LEFT JOIN suggestions sug ON sug.pid = p.id
LEFT JOIN tracks t ON sug.tid = t.id
LEFT JOIN subscribers sub ON sub.id = p.sid
LEFT JOIN playback pb ON pb.sid = sub.id
WHERE p.created_at = CURRENT_DATE
  AND sub.license = ${lck}
  AND sug.consumed = FALSE
  AND (
    pb.last_tid IS NULL -- No previous playback record
    OR sug.added_at >= (
      SELECT sug2.added_at
      FROM suggestions sug2
      WHERE sug2.pid = pb.last_pid 
        AND sug2.tid = pb.last_tid
    )
  )
ORDER BY sug.added_at ASC
    `
  ).flatMap((t) => t);

  const countOfSuggestions = await getRemainingSuggestionsCount(lck);
  if (countOfSuggestions <= 10) {
    // In case there are less than 10 suggestions available up next, we are scheduling
    // a task in the background to generate some additional music.
    ch.sendToQueue(
      "acura",
      Buffer.from(
        JSON.stringify({
          license: request.cookies.get("lck")?.value,
          prompt:
            `I am the owner of a restaurant called "Martini Royale" at the ` +
            `center of Yerevan, Armenia. It is a place where people can enjoy ` +
            `a quiet meal under some jazzy, classical, and some smooth pop music. ` +
            `Help me generate some stuff.`,
        })
      )
    );
  }

  return NextResponse.json(queue, { status: 200 });
}
