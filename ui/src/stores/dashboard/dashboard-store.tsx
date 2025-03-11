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
  lastFetchTimestamp: number; // New field to track when we last fetched
};

export type DashboardActions = {
  play: () => void;
  pause: () => void;
  next: () => void;
  setQueue: (tracks: Track[]) => void;
  addToQueue: (tracks: Track[]) => void; // New method to properly add tracks
  setCurrentTrackId: (id: number) => void;
  updateLastFetchTimestamp: () => void; // New method to update fetch timestamp
};

export type DashboardStore = DashboardState & DashboardActions;

export const defaultInitState: DashboardState = {
  queue: [],
  isPlaying: false,
  currentTrack: null,
  currentTrackId: -1,
  lastFetchTimestamp: 0,
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
            (s) => {
              // Handle initial queue population
              if (s.queue.length === 0) {
                return {
                  queue: tracks,
                  currentTrackId: tracks[0]?.id ?? -1,
                  currentTrack: tracks[0] ?? null,
                  lastFetchTimestamp: Date.now(),
                };
              }
              
              // Handle adding tracks to existing queue
              return {
                queue: tracks,
                // Don't change currentTrackId if already playing something
                currentTrackId: s.currentTrackId >= 0 ? s.currentTrackId : tracks[0]?.id ?? -1,
                currentTrack: s.currentTrack ?? tracks[0] ?? null,
                lastFetchTimestamp: Date.now(),
              };
            },
            undefined,
            "dashboard-store/setQueue"
          ),
        addToQueue: (newTracks) =>
          set(
            (state) => {
              // Deduplicate tracks based on track ID
              const existingIds = new Set(state.queue.map((track) => track.id));
              const filteredTracks = newTracks.filter((track) => !existingIds.has(track.id));
              
              if (filteredTracks.length === 0) {
                return {}; // No changes if no new tracks
              }
              
              const updatedQueue = [...state.queue, ...filteredTracks];
              
              return {
                queue: updatedQueue,
                currentTrackId: state.currentTrackId >= 0 ? state.currentTrackId : updatedQueue[0]?.id ?? -1,
                currentTrack: state.currentTrack ?? updatedQueue[0] ?? null,
              };
            },
            undefined,
            "dashboard-store/addToQueue"
          ),
        updateLastFetchTimestamp: () =>
          set(
            () => ({
              lastFetchTimestamp: Date.now(),
            }),
            undefined,
            "dashboard-store/updateLastFetchTimestamp"
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
