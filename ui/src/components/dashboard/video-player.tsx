"use client";

import "./styles/video-player.css";

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import { Skeleton } from "@heroui/react";
import ReactPlayer from "react-player";

export default function VideoPlayer() {
  const { currentTrack, pause, play, isPlaying, next } = useDashboardStore(
    (s) => s
  );

  // TODO: Finalize this after implementing proper handling for URLs
  return !currentTrack ? (
    <Skeleton className="w-full md:w-[38rem] h-[20rem] rounded-md" />
  ) : (
    <div className="w-full md:w-[38rem] h-full">
      <ReactPlayer
        onPause={() => pause()}
        onPlay={() => play()}
        // in case the video was not actually embeddable
        onError={() => next()}
        stopOnUnmount
        id={"player"}
        onEnded={() => next()}
        url={currentTrack.uri}
        width={"100%"}
        height={"100%"}
        playing={isPlaying}
      />
    </div>
  );
}
