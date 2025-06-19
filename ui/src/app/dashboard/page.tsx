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
import Player from "@/src/components/dashboard/player";
import PlaybackQueue from "@/src/components/dashboard/playback-queue";
import CurrentPlaybackInfo from "@/src/components/dashboard/current-playback-info";
// import StatsGroup from "@/src/components/dashboard/stats-group";

export default function DashboardContent() {
  return (
    <div className="w-full h-full gap-8 flex flex-col items-center">
      {/* <StatsGroup /> */}

      <div className="w-full flex flex-row gap-3">
        <CurrentPlaybackInfo />
      </div>

      <div className="w-full h-fit flex-col gap-6 flex md:flex-row md:justify-between">
        <PlaybackQueue />
        <Player />
      </div>
    </div>
  );
}
