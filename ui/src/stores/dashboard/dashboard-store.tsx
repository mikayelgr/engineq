// src/stores/counter-store.ts
import { createStore } from "zustand/vanilla";
import { devtools } from "zustand/middleware";

export type Track = {
  id: number;
  title: string;
  artist: string;
  explicit: boolean;
  duration: string;
  image: string;
  uri: string;
};

export type DashboardState = {
  queue: Track[];
  isPlaying: boolean;
  currentTrackId: number;
  currentTrack: Track | null;
};

export type DashboardActions = {
  play: () => void;
  pause: () => void;
  next: () => void;
  setQueue: (tracks: Track[]) => void;
  setCurrentTrackId: (id: number) => void;
};

export type DashboardStore = DashboardState & DashboardActions;

export const defaultInitState: DashboardState = {
  queue: [],
  isPlaying: false,
  currentTrack: null,
  currentTrackId: -1,
};

export const createDashboardStore = (
  initState: DashboardState = defaultInitState
) => {
  return createStore<DashboardStore>()(
    devtools(
      (set) => ({
        ...initState,
        next: () =>
          set(
            ({ queue, setCurrentTrackId }) => {
              queue.shift();
              if (queue.length !== 0) setCurrentTrackId(queue[0].id);
              return { queue, isPlaying: queue.length !== 0 };
            },
            undefined,
            "dashboard-store/next"
          ), // automatically removing the first played element
        setQueue: (tracks) =>
          set(
            (s) => ({
              queue: tracks,
              currentTrackId: s.queue.length === 0 ? tracks[0]?.id : -1,
            }),
            undefined,
            "dashboard-store/setQueue"
          ),
        pause: () =>
          set(() => ({ isPlaying: false }), undefined, "dashboard-store/pause"),
        play: () =>
          set(
            ({ queue, setCurrentTrackId }) => {
              if (queue.length !== 0) setCurrentTrackId(queue[0].id);
              return { isPlaying: queue.length !== 0 };
            },
            undefined,
            "dashboard-store/play"
          ),
        setCurrentTrackId: (tid) =>
          set(
            ({ queue, currentTrackId }) => {
              const currentTrackIndex = queue.findIndex(
                (t) => t.id === currentTrackId
              );
              const newTrackIndex = queue.findIndex((t) => t.id === tid);
              return {
                queue:
                  // Skipping over the rest of the songs
                  newTrackIndex > currentTrackIndex
                    ? queue.slice(newTrackIndex)
                    : queue,
                currentTrackId: tid,
                currentTrack: queue.find((t) => t.id === tid),
              };
            },
            undefined,
            "dashboard-store/setCurrentTrackId"
          ),
      }),
      { name: "dashboard-store" }
    )
  );
};
