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

// src/stores/counter-store.ts
import { createStore } from "zustand/vanilla";
import { devtools } from "zustand/middleware";

export type Suggestion = Track & {
  suggestion_id: string;
};

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
  queue: Suggestion[];
  isMuted: boolean;
  isPlaying: boolean;
  currentSuggestionId: string | null;
  currentSuggestion: Suggestion | null;
  lastFetchTimestamp: number; // New field to track when we last fetched
};

export type DashboardActions = {
  play: () => void;
  pause: () => void;
  next: () => void;
  toggleMuted: () => void;
  setQueue: (suggestions: Suggestion[]) => void;
  addToQueue: (suggestions: Suggestion[]) => void; // New method to properly add tracks
  setCurrentSuggestionId: (id: string) => void;
  updateLastFetchTimestamp: () => void; // New method to update fetch timestamp
};

export type DashboardStore = DashboardState & DashboardActions;

export const defaultInitState: DashboardState = {
  queue: [],
  isMuted: false,
  isPlaying: false,
  currentSuggestion: null,
  currentSuggestionId: null,
  lastFetchTimestamp: 0,
};

export const createDashboardStore = (
  initState: DashboardState = defaultInitState
) => {
  return createStore<DashboardStore>()(
    devtools(
      (set) => ({
        ...initState,
        toggleMuted: () =>
          set(
            ({ isMuted }) => ({ isMuted: !isMuted }),
            undefined,
            "dashboard-store/toggleMuted"
          ),
        next: () =>
          set(
            ({ queue, setCurrentSuggestionId }) => {
              queue.shift();
              if (queue.length !== 0)
                setCurrentSuggestionId(queue[0].suggestion_id);
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
                  currentSuggestionId: tracks[0]?.suggestion_id ?? null,
                  currentSuggestion: tracks[0] ?? null,
                  lastFetchTimestamp: Date.now(),
                };
              }

              // Handle adding tracks to existing queue
              return {
                queue: tracks,
                // Don't change currentTrackId if already playing something
                currentSuggestionId:
                  s.currentSuggestionId !== null
                    ? s.currentSuggestionId
                    : (tracks[0]?.suggestion_id ?? null),
                currentSuggestion: s.currentSuggestion ?? tracks[0] ?? null,
                lastFetchTimestamp: Date.now(),
              };
            },
            undefined,
            "dashboard-store/setQueue"
          ),
        addToQueue: (newTracks) =>
          set(
            (state) => {
              // Deduplicate tracks based on suggestion ID
              const existingIds = new Set(
                state.queue.map((s) => s.suggestion_id)
              );
              const filteredSuggestions = newTracks.filter(
                (s) => !existingIds.has(s.suggestion_id)
              );

              if (filteredSuggestions.length === 0) {
                return {}; // No changes if no new tracks
              }

              const updatedQueue = [...state.queue, ...filteredSuggestions];

              return {
                queue: updatedQueue,
                currentSuggestionId:
                  state.currentSuggestionId !== null
                    ? state.currentSuggestionId
                    : (updatedQueue[0]?.suggestion_id ?? -1),
                currentSuggestion:
                  state.currentSuggestion ?? updatedQueue[0] ?? null,
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
            ({ queue, setCurrentSuggestionId }) => {
              if (queue.length !== 0)
                setCurrentSuggestionId(queue[0].suggestion_id);
              return { isPlaying: queue.length !== 0 };
            },
            undefined,
            "dashboard-store/play"
          ),
        setCurrentSuggestionId: (suggestionId) =>
          set(
            ({ queue, currentSuggestionId: currentTrackId }) => {
              const currentSuggestionIndex = queue.findIndex(
                (s) => s.suggestion_id === currentTrackId
              );
              const newTrackIndex = queue.findIndex(
                (s) => s.suggestion_id === suggestionId
              );
              return {
                queue:
                  // Skipping over the rest of the songs
                  newTrackIndex > currentSuggestionIndex
                    ? queue.slice(newTrackIndex)
                    : queue,
                currentSuggestionId: suggestionId,
                currentSuggestion: queue.find(
                  (s) => s.suggestion_id === suggestionId
                ),
              };
            },
            undefined,
            "dashboard-store/setCurrentSuggestionId"
          ),
      }),
      { name: "dashboard-store" }
    )
  );
};
