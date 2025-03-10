"use client";

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import { Button, ButtonGroup } from "@heroui/react";
import { Pause, Play, SkipForward } from "lucide-react";
import { useEffect } from "react";

export default function PlaybackControl() {
  const { pause, play, next, isPlaying, currentTrackId, queue } =
    useDashboardStore((s) => s);

  useEffect(() => {
    async function _() {
      if (currentTrackId > 0)
        await fetch(`/api/update-last-played?tid=${currentTrackId}`);
    }

    _();
  }, [currentTrackId]);

  return (
    <ButtonGroup>
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
