"use client";

import { useEffect, useState } from "react";
import StatsCard from "./stats-card";
import { format, formatDuration, secondsToHours } from "date-fns";

export default function StatsGroup() {
  const [stats, setStats] = useState<Record<string, number | string> | null>(
    null
  );

  async function loadStats() {
    const req = await fetch("/api/stats");
    const res = await req.json();
    setStats(res);
  }

  useEffect(() => {
    loadStats();

    return () => {
      setStats(null);
    };
  }, []);

  return (
    <div className="grid grid-cols-1 row-span-1 w-full gap-4 md:grid-cols-3 md:grid-rows-1 grid-rows-3 grid-flow-row">
      <StatsCard
        content="Time Saved on Music Research"
        stats={
          stats?.timeSavings
            ? format(stats?.timeSavings as number, "h") + " hours"
            : "No Data"
        }
      />
      <StatsCard
        content="Money Saved"
        stats={(stats?.costSavings as string | null) || "No Data"}
      />
      <StatsCard
        content="Hours of Music Generated"
        stats={
          stats?.costSavings
            ? secondsToHours(stats?.totalGeneratedSeconds as number) + " hours"
            : "No Data"
        }
      />
    </div>
  );
}
