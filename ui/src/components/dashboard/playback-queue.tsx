"use client";

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import PlaybackControl from "./playback-control";
import PlaybackQueueTrack from "./playback-queue-track";
import { ScrollShadow, Spinner } from "@heroui/react";
import { useEffect, useState } from "react";

export default function PlaybackQueue() {
  const { queue, currentTrackId, setQueue } = useDashboardStore((s) => s);
  const [isFetching, setIsFetching] = useState(false);

  async function loadTracks(ctid: string | null = null) {
    setIsFetching(true);
    const request = await fetch(
      `/api/tracklist?` + (ctid ? `tid=${ctid}` : "")
    );
    const latest = await request.json();
    setQueue(queue.concat(latest));
    setIsFetching(false);
  }

  useEffect(() => {
    loadTracks(); // initial useffect for loading the tracks
  }, []);

  useEffect(() => {
    if (queue.length <= 10 && currentTrackId >= 0) {
      loadTracks(); // load additional tracks
    }
  }, [currentTrackId]);

  return (
    <div className="h-[20rem] w-full md:w-[24rem] rounded-md border-gray-600 bg-secondary-100 bg-opacity-40">
      <div className="px-4 pt-4 gap-4 w-full flex flex-col h-full">
        <div className="w-full flex items-center justify-between">
          <h1 className="text-2xl font-bold">Queue</h1>
          <PlaybackControl />
        </div>

        <div className="h-full rounded-xl overflow-y-auto">
          <ScrollShadow id="queue" className="flex flex-col p-2 gap-2 w-full">
            {queue &&
              queue.map((t) => t && <PlaybackQueueTrack key={t.id} {...t} />)}

            {(!queue || queue.length === 0) && (
              <div className="w-full h-full flex flex-col gap-4 items-center justify-center">
                <Spinner color="secondary" variant="spinner" />

                {/* Assuming that this is the first time they are using the application */}
                {!isFetching && (
                  <p className="text-center text-sm">
                    We are loading your recommendations. Refresh the page after
                    about 5 minutes if this is your first time using the
                    software 😊
                  </p>
                )}
              </div>
            )}
          </ScrollShadow>
        </div>
      </div>
    </div>
  );
}
