"use client";

import "./styles/player.css";

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import { Skeleton } from "@heroui/react";
import ReactPlayer from "react-player";

export default function Player() {
  const { currentTrack, pause, play, isPlaying, next, isMuted } =
    useDashboardStore((s) => s);

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
        controls
        muted={isMuted}
        onEnded={() => next()}
        url={currentTrack.uri}
        width={"100%"}
        height={"100%"}
        playing={isPlaying}
      />
    </div>
  );
}
