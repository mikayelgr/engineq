"use client";

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import { title } from "../primitives";

export default function CurrentPlaybackInfo() {
  const { currentTrack } = useDashboardStore((s) => s);

  return (
    <div className="w-full">
      <h1 className={title({ size: "sm" })}>
        {currentTrack ? "Currently Playing" : "Nothing is Playing Right Now"}
      </h1>
      <p className="w-full text-gray-400">
        {currentTrack ? (
          <>
            {currentTrack?.artist} - {currentTrack?.title}
          </>
        ) : (
          "Click the play button when you are ready."
        )}
      </p>
    </div>
  );
}
