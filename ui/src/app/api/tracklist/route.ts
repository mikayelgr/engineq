import { NextRequest, NextResponse } from "next/server";
import amqplib from "amqplib";
import { sql } from "@/src/lib/sql";

let mq: amqplib.ChannelModel | null = null;
let ch: amqplib.Channel | null = null;

async function getRemainingSuggestionsCount(lck: string) {
  const result = await sql`
    SELECT COUNT(*) as count FROM playlists p
    LEFT JOIN subscribers sub ON sub.id = p.sid
    LEFT JOIN suggestions sug ON sug.pid = p.id
    LEFT JOIN tracks t ON sug.tid = t.id
    LEFT JOIN playback pb ON pb.sid = sub.id
    WHERE p.id = COALESCE(pb.last_pid, p.id) 
      AND sub.license = ${lck}
      AND (
        -- If this is the same playlist they were on before, start after their last position
        (p.id = pb.last_pid AND sug.added_at >= (
          SELECT added_at 
          FROM suggestions 
          WHERE pid = pb.last_pid AND tid = pb.last_tid
        ))
        -- If this is a different playlist, show all tracks
        OR (p.id != pb.last_pid)
      )`;
  return result[0].count;
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
JOIN suggestions sug ON sug.pid = p.id
JOIN tracks t ON sug.tid = t.id
JOIN subscribers sub ON sub.id = p.sid
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
