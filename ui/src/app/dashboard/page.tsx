import Player from "@/src/components/dashboard/player";
import PlaybackQueue from "@/src/components/dashboard/playback-queue";
import CurrentPlaybackInfo from "@/src/components/dashboard/current-playback-info";
import StatsGroup from "@/src/components/dashboard/stats-group";

export default function DashboardContent() {
  return (
    <div className="w-full h-full gap-8 flex flex-col items-center">
      <StatsGroup />

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
