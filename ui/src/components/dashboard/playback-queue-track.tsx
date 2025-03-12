import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import { Track } from "@/src/stores/dashboard/dashboard-store";
import { Card, CardHeader, Image, Skeleton } from "@heroui/react";
import clsx from "clsx";

interface PlaybackQueueTrackProps extends Track {
  asSkeleton?: boolean;
}

const truncateString = (string = "", maxLength = 20) =>
  string.length > maxLength ? `${string.substring(0, maxLength)}…` : string;

export default function PlaybackQueueTrack(props: PlaybackQueueTrackProps) {
  const { currentTrackId, setCurrentTrackId } = useDashboardStore((s) => s);

  return (
    <Card
      {...(props.asSkeleton && { as: Skeleton })}
      className={clsx(
        "transition-all duration-200",
        currentTrackId === props.id &&
          "shadow-lg bg-primary/20 ring-2 ring-primary/20"
      )}
      isPressable
      onPress={() => setCurrentTrackId(props.id)}
    >
      <CardHeader className="gap-2 w-full">
        <Image
          alt="heroui logo"
          height={40}
          radius="sm"
          className="w-40"
          src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRfr1IXhAWefDdclacaEwS8VXBQ02xNeoHPog&s"
          width={40}
        />

        <div className="flex flex-col items-start">
          <div className="flex w-fit flex-row gap-1 items-center">
            <p className="text-md w-fit text-left">{truncateString(props.title)}</p>
            {props.explicit && (
              <p className="text-xs w-[1rem] h-[1rem] flex items-center justify-center rounded-sm bg-gray-500 text-white font-bold">
                E
              </p>
            )}
          </div>

          <p className="text-small text-default-500">{truncateString(props.artist)}</p>
        </div>
      </CardHeader>
    </Card>
  );
}
