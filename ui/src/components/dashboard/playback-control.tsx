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
import { Button, ButtonGroup } from "@heroui/react";
import { Pause, Play, SkipForward, Volume2, VolumeOff } from "lucide-react";
import { useEffect } from "react";

export default function PlaybackControl() {
  const {
    pause,
    play,
    next,
    isPlaying,
    currentSuggestionId,
    queue,
    isMuted,
    toggleMuted,
  } = useDashboardStore((s) => s);

  useEffect(() => {
    async function _() {
      if (currentSuggestionId)
        await fetch(`/api/update-last-played?sid=${currentSuggestionId}`);
    }

    _();
  }, [currentSuggestionId]);

  return (
    <ButtonGroup>
      <Button
        onPress={() => toggleMuted()}
        size="sm"
        color="primary"
        variant="flat"
        isIconOnly
      >
        {isMuted ? <VolumeOff size={16} /> : <Volume2 size={16} />}
      </Button>
      <Button
        variant="flat"
        color="primary"
        size="sm"
        onPress={() => {
          if (isPlaying) pause();
          else play();
        }}
        isDisabled={queue.length === 0}
        isIconOnly
      >
        {isPlaying ? <Pause size={16} /> : <Play size={16} />}
      </Button>
      <Button
        variant="flat"
        color="primary"
        size="sm"
        isDisabled={queue.length === 0}
        onPress={async () => {
          next();
        }}
        isIconOnly
      >
        <SkipForward size={16} />
      </Button>
    </ButtonGroup>
  );
}
