// src/stores/counter-store.ts
import { createStore } from "zustand/vanilla";
import { Queue } from "@datastructures-js/queue";

// used for type inference and never used directly
const __trackQueue = new Queue<Track>();

type Track = {
  id: number;
  title: string;
  artist: string;
  youtubeUrl: string;
};

export type DashboardState = {
  isPlaying: boolean;
  queue: typeof __trackQueue;
};

export type DashboardActions = {
  play: () => void;
  pause: () => void;
  next: () => void;
};

export type DashboardStore = DashboardState & DashboardActions;

export const defaultInitState: DashboardState = {
  isPlaying: true, // autoplay by default
  queue: new Queue([]),
};

export const createDashboardStore = (
  initState: DashboardState = defaultInitState
) => {
  return createStore<DashboardStore>()((set, get) => ({
    ...initState,
    next: () => get().queue.pop(),
    pause: () => set((_state) => ({ isPlaying: false })),
    play: () => set((_state) => ({ isPlaying: true })),
  }));
};
