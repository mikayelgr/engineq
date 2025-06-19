// EngineQ: An AI-enabled music management system.
// Copyright (C) 2025  Mikayel Grigoryan
// 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
// 
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
// 
// For inquiries, contact: michael.grigoryan25@gmail.com
"use client";

import "./styles/player.css";

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import { Skeleton } from "@heroui/react";
import ReactPlayer from "react-player";

export default function Player() {
  const { currentSuggestion: currentTrack, pause, play, isPlaying, next, isMuted } =
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
