"use client";

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import PlaybackControl from "./playback-control";
import PlaybackQueueTrack from "./playback-queue-track";
import { ScrollShadow, Spinner } from "@heroui/react";
import { useEffect, useRef, useState } from "react";

export default function PlaybackQueue() {
  const { queue, currentTrackId, addToQueue } = useDashboardStore((s) => s);

  const [isFetching, setIsFetching] = useState(false);
  const initialLoadComplete = useRef(false);
  const lastQueueLength = useRef(0);
  const fetchingRef = useRef(false);

  async function loadTracks(ctid: string | null = null) {
    // Use ref to track fetching state to prevent race conditions
    if (fetchingRef.current) return;

    fetchingRef.current = true;
    setIsFetching(true);

    try {
      const request = await fetch(
        `/api/tracklist?` + (ctid ? `tid=${ctid}` : "")
      );
      const latest = await request.json();

      // Update the last queue length ref to prevent infinite loops
      lastQueueLength.current =
        queue.length +
        latest.filter((track) => {
          // Quick duplicate check for length estimation
          return !queue.some((q) => q.id === track.id);
        }).length;

      // Use the addToQueue method which handles deduplication internally
      addToQueue(latest);
    } catch (error) {
      console.error("Error loading tracks:", error);
    } finally {
      setIsFetching(false);
      fetchingRef.current = false;
    }
  }

  // Initial load effect
  useEffect(() => {
    if (!initialLoadComplete.current) {
      loadTracks();
      initialLoadComplete.current = true;
    }
  }, []);

  // Effect for loading more tracks when needed
  useEffect(() => {
    // Only proceed if initial load is done, not currently fetching,
    // and we're not caught in an infinite loop (queue length changed)
    if (
      initialLoadComplete.current &&
      queue.length <= 10 &&
      currentTrackId >= 0 &&
      !fetchingRef.current &&
      queue.length !== lastQueueLength.current
    ) {
      loadTracks();
    }

    // Update lastQueueLength to current value whenever queue changes
    // This prevents the effect from running again if the fetch didn't add new items
    if (queue.length !== lastQueueLength.current) {
      lastQueueLength.current = queue.length;
    }
  }, [queue.length, currentTrackId]);

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
