import { sql } from "@/src/lib/sql";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const lck = req.cookies.get("lck")?.value!;
  const stats = await sql`
  select sum(t.duration) as seconds_sum, count(t.id) as count_sum from playlists p
  left join subscribers sub on sub.id = p.sid
  left join suggestions sug on sug.pid = p.id
  left join tracks        t on t.id = sug.tid
  where sub.license = ${lck}
  `;

  return NextResponse.json({
    totalGeneratedSeconds: Number(stats[0].seconds_sum),
    // 63 seconds to research a single song on average
    timeSavings: Number(stats[0].count_sum) * 63,
    // If an hour of DJ time costs $100, then I need to calculate the cost per second.
    // $100 per hour
    // = $100 ÷ 60 minutes = $1.67 per minute
    // = $1.67 ÷ 60 seconds = $0.028 per second (rounded to 3 decimal places)
    // Therefore, one second of DJ time costs approximately $0.028 or 2.8 cents.
    //
    // Author is Claude-3.7 Sonnet. I was too tired to think myself.
    costSavings: `${Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(stats[0].seconds_sum! * 0.028)}`,
  });
}
