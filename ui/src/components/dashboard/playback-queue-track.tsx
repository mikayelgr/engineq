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
import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import { Suggestion } from "@/src/stores/dashboard/dashboard-store";
import { Card, CardHeader, Image, Skeleton } from "@heroui/react";
import clsx from "clsx";

interface PlaybackQueueTrackProps extends Suggestion {
  asSkeleton?: boolean;
}

const truncateString = (string = "", maxLength = 20) =>
  string.length > maxLength ? `${string.substring(0, maxLength)}…` : string;

export default function PlaybackQueueTrack(props: PlaybackQueueTrackProps) {
  const {
    currentSuggestionId: currentTrackId,
    setCurrentSuggestionId: setCurrentTrackId,
  } = useDashboardStore((s) => s);

  return (
    <Card
      {...(props.asSkeleton && { as: Skeleton })}
      className={clsx(
        "transition-all duration-200",
        currentTrackId === props.suggestion_id &&
          "shadow-lg bg-primary/20 ring-2 ring-primary/20"
      )}
      isPressable
      onPress={() => setCurrentTrackId(props.suggestion_id)}
    >
      <CardHeader className="gap-2 w-full">
        <Image
          alt="heroui logo"
          height={40}
          radius="sm"
          className="w-40"
          src={
            props.image ||
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRfr1IXhAWefDdclacaEwS8VXBQ02xNeoHPog&s"
          }
          width={40}
        />

        <div className="flex flex-col items-start">
          <div className="flex w-fit flex-row gap-1 items-center">
            <p className="text-md w-fit text-left">
              {truncateString(props.title)}
            </p>
            {props.explicit && (
              <p className="text-xs w-[1rem] h-[1rem] flex items-center justify-center rounded-sm bg-gray-500 text-white font-bold">
                E
              </p>
            )}
          </div>

          <p className="text-small text-default-500">
            {truncateString(props.artist)}
          </p>
        </div>
      </CardHeader>
    </Card>
  );
}
