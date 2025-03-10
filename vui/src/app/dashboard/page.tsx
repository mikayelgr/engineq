"use client";

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import "./styles.css";

import { title } from "@/src/components/primitives";
import { Button, ButtonGroup, Card } from "@heroui/react";
import { Pause, Play, SkipBack, SkipForward } from "lucide-react";
import ReactPlayer from "react-player";

export default function DashboardContent() {
  const store = useDashboardStore((s) => s);

  return (
    <div className="px-4 w-full mt-6 grid grid-cols-1 sm:grid-cols-3 gap-6">
      {/* Stats Section */}
      <div>
        <Card className="h-full">
          <div className="p-4">
            <h4 className="text-lg font-semibold">
              Time Saved on Music Research
            </h4>
            <p className="text-2xl">150 hours</p>
          </div>
        </Card>
      </div>

      <div>
        <Card className="h-full">
          <div className="p-4">
            <h4 className="text-lg font-semibold">Money Saved</h4>
            <p className="text-2xl">$2,500</p>
          </div>
        </Card>
      </div>

      <div>
        <Card>
          <div className="p-4">
            <h4 className="text-lg font-semibold">Hours of Music Generated</h4>
            <p className="text-2xl">1,200 hours</p>
          </div>
        </Card>
      </div>

      <div className="col-span-2">
        <h1 className={title({ size: "sm" })}>Currently Playing</h1>
        <p className="w-full text-gray-400">
          Rich Gang - Tapout ft. Lil Wayne, Birdman, Mack Maine, Nicki Minaj,
          Future
        </p>
      </div>

      <div className="col-span-1 items-center flex justify-end gap-2">
        <ButtonGroup>
          <Button isIconOnly>
            <SkipBack size={16} />
          </Button>
          <Button
            onPress={() => {
              if (store.isPlaying) store.pause();
              else store.play();
            }}
            isIconOnly
          >
            {store.isPlaying ? <Pause size={16} /> : <Play size={16} />}
          </Button>
          <Button onPress={() => store.next()} isIconOnly>
            <SkipForward size={16} />
          </Button>
        </ButtonGroup>
      </div>

      {/* Video and Queue Section */}
      <div className="sm:col-span-3 w-full flex-col md:flex-row flex gap-6">
        {/* YouTube Video Player */}
        <ReactPlayer
          height={"25rem"}
          onEnded={() => store.next()}
          width={"100%"}
          playing={store.isPlaying}
          controls
          id={"player"}
          url={
            "https://www.youtube.com/watch?v=OGtlq-cvIS4&ab_channel=RichGangVEVO&autoplay=1"
          }
        />

        {/* Queue */}
        <div className="bg-gray-500 w-full md:w-[32rem] h-[25rem] bg-opacity-50 p-4 rounded-lg overflow-y-auto">
          <h5 className="text-xl font-semibold">Queue</h5>
          <div>
            <ul className="space-y-2">
              <li>Song 1</li>
              <li>Song 2</li>
              <li>Song 3</li>
              <li>Song 4</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
              <li>Song 5</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
