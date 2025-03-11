"use client";

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import PlaybackControl from "./playback-control";
import PlaybackQueueTrack from "./playback-queue-track";
import { ScrollShadow, Spinner } from "@heroui/react";
import { useEffect, useState, useRef } from "react";

export default function PlaybackQueue() {
  const { queue, currentTrackId, setQueue } = useDashboardStore((s) => s);
  const [isFetching, setIsFetching] = useState(false);
  const initialLoadComplete = useRef(false);

  async function loadTracks(ctid: string | null = null) {
    if (isFetching) return; // Prevent concurrent fetches
    setIsFetching(true);

    try {
      const request = await fetch(
        `/api/tracklist?` + (ctid ? `tid=${ctid}` : "")
      );
      const latest = await request.json();

      // Deduplicate tracks based on track ID
      const existingIds = new Set(queue.map((track) => track.id));
      const newTracks = latest.filter((track: any) => !existingIds.has(track.id));

      if (newTracks.length > 0) {
        setQueue([...queue, ...newTracks]);
      }
    } catch (error) {
      console.error("Error loading tracks:", error);
    } finally {
      setIsFetching(false);
    }
  }

  useEffect(() => {
    // Only load tracks once on initial render
    if (!initialLoadComplete.current) {
      loadTracks();
      initialLoadComplete.current = true;
    }
  }, []);

  useEffect(() => {
    // Only load more tracks when queue is running low and not in initial loading
    if (
      initialLoadComplete.current &&
      queue.length <= 10 &&
      currentTrackId >= 0 &&
      !isFetching
    ) {
      loadTracks();
    }
  }, [currentTrackId, queue.length, isFetching]);

  return (
    <div className="h-[20rem] w-full md:w-[24rem] rounded-md border-gray-600 bg-secondary-100 bg-opacity-40">
      <div className="px-4 pt-4 gap-4 w-full flex flex-col h-full">
        <div className="w-full flex items-center justify-between">
          <h1 className="text-2xl font-bold">Queue</h1>
          <PlaybackControl />
        </div>

        <div className="h-full rounded-xl overflow-hidden">
          <ScrollShadow
            id="queue"
            className="flex flex-col p-2 gap-2 w-full h-full overflow-y-auto"
          >
            {queue && queue.length > 0 ? (
              <div className="w-full flex flex-col gap-2">
                {queue.map(
                  (t) => t && <PlaybackQueueTrack key={t.id} {...t} />
                )}
              </div>
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center">
                <Spinner color="secondary" variant="spinner" size="lg" />

                {!isFetching && (
                  <p className="text-center text-sm max-w-[80%] mt-4">
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
