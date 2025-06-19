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

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import { title } from "../primitives";

export default function CurrentPlaybackInfo() {
  const { currentSuggestion: currentTrack } = useDashboardStore((s) => s);

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
