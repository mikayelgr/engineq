"use client";

import "./styles/video-player.css";

import { useDashboardStore } from "@/src/providers/dashboard/dashboard-store-provider";
import { Skeleton } from "@heroui/react";
import Script from "next/script";
import { useEffect, useRef, useState } from "react";

const options = {
  width: "100%",
  height: "100%",
};

export default function VideoPlayer() {
  const embedRef = useRef<HTMLDivElement>(null);
  const [embedController, setEmbedController] = useState<any>(null);
  const [isApiReady, setIsApiReady] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const { currentTrack, pause, play, isPlaying, next } = useDashboardStore(
    (s) => s
  );

  // Initialize controller when API is ready and ref exists
  useEffect(() => {
    if (!isApiReady || !embedRef.current) return;

    const callback = (EmbedController: any) => {
      setEmbedController(EmbedController);
      setIsLoading(false);

      EmbedController.addListener("ready", () => play());
      EmbedController.addListener("playback_update", (state: any) => {
        if (state.data.isPaused) pause();
        else play();

        // means we need to switch to the next track
        if (state.data.isPaused && isPlaying) next();
      });

      EmbedController.addListener("error", (error: any) => {
        console.error("Spotify player error:", error);
        setIsLoading(false);
      });
    };

    try {
      (window as any).onSpotifyIframeApiReady = (IFrameAPI: any) => {
        IFrameAPI.createController(embedRef.current, options, callback);
      };
    } catch (error) {
      console.error("Error creating Spotify controller:", error);
      setIsLoading(false);
    }
  }, [isApiReady, embedRef]);

  useEffect(() => {
    if (!embedController) return;

    if (isPlaying) embedController.play();
    else embedController.pause();
  }, [embedController, isPlaying]);

  // Load track when controller is ready and track changes
  useEffect(() => {
    if (!embedController || !currentTrack?.uri) return;

    setIsLoading(true);
    try {
      let uri = currentTrack.uri;

      // Handle different URI formats
      if (uri.includes("/embed")) {
        // Format: https://open.spotify.com/embed/track/1234
        const parts = uri.split("/embed")[1].split("/");
        uri = `spotify:${parts[1]}:${parts[2]}`;
      } else if (uri.startsWith("https://open.spotify.com/")) {
        // Format: https://open.spotify.com/track/1234
        const parts = uri.replace("https://open.spotify.com/", "").split("/");
        uri = `spotify:${parts[0]}:${parts[1]}`;
      }

      embedController.loadUri(uri);
      embedController.play();
    } catch (error) {
      console.error("Error loading track:", error);
      next(); // Skip to next track on error
    } finally {
      setIsLoading(false);
    }
  }, [embedController, currentTrack, next]);

  // Handle script load event
  const handleScriptLoad = () => setIsApiReady(true);

  return (
    <div className="w-full md:w-[38rem] h-[20rem] relative">
      {(!currentTrack || isLoading) && (
        <Skeleton className="w-full h-full rounded-md absolute top-0 left-0 z-10" />
      )}
      <div ref={embedRef} id="embed-iframe" className="w-full h-full"></div>
      <Script
        src="https://open.spotify.com/embed/iframe-api/v1"
        onLoad={handleScriptLoad}
        strategy="afterInteractive"
      />
    </div>
  );
}
