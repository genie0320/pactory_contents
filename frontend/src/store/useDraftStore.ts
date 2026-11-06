import { create } from 'zustand';
import type { BlueprintResponse, SeedCandidateItem } from '../api/client';

interface DraftState {
  // Wizard Step: 1 = Topic/Direction, 2 = Seed Selection, 3 = Blueprint & Draft Generation
  step: 1 | 2 | 3;
  topic: string;
  direction: string;
  targetArchetype: string;
  candidates: SeedCandidateItem[];
  selectedSeedIds: string[];
  blueprint: BlueprintResponse | null;
  draftContent: string;
  creationId: string | null;

  // Loading flags
  isSearchingSeeds: boolean;
  isGeneratingBlueprint: boolean;
  isSynthesizing: boolean;

  // Actions
  setStep: (step: 1 | 2 | 3) => void;
  setTopic: (topic: string) => void;
  setDirection: (direction: string) => void;
  setTargetArchetype: (archetype: string) => void;
  toggleSeed: (docId: string) => void;
  setSelectedSeedIds: (ids: string[]) => void;
  setCandidates: (candidates: SeedCandidateItem[]) => void;
  setBlueprint: (blueprint: BlueprintResponse | null) => void;
  setDraftContent: (content: string) => void;
  setCreationId: (id: string | null) => void;
  setLoading: (key: 'isSearchingSeeds' | 'isGeneratingBlueprint' | 'isSynthesizing', value: boolean) => void;

  // Clean reset
  resetDraft: () => void;
}

const initialState = {
  step: 1 as const,
  topic: '',
  direction: '',
  targetArchetype: 'PRACTICAL_GUIDE',
  candidates: [],
  selectedSeedIds: [],
  blueprint: null,
  draftContent: '',
  creationId: null,
  isSearchingSeeds: false,
  isGeneratingBlueprint: false,
  isSynthesizing: false,
};

export const useDraftStore = create<DraftState>((set) => ({
  ...initialState,

  setStep: (step) => set({ step }),
  setTopic: (topic) => set({ topic }),
  setDirection: (direction) => set({ direction }),
  setTargetArchetype: (targetArchetype) => set({ targetArchetype }),

  toggleSeed: (docId) =>
    set((state) => {
      const exists = state.selectedSeedIds.includes(docId);
      const next = exists
        ? state.selectedSeedIds.filter((id) => id !== docId)
        : [...state.selectedSeedIds, docId];
      return { selectedSeedIds: next };
    }),

  setSelectedSeedIds: (selectedSeedIds) => set({ selectedSeedIds }),
  setCandidates: (candidates) => set({ candidates }),
  setBlueprint: (blueprint) => set({ blueprint }),
  setDraftContent: (draftContent) => set({ draftContent }),
  setCreationId: (creationId) => set({ creationId }),
  setLoading: (key, value) => set({ [key]: value }),

  resetDraft: () => {
    set({ ...initialState });
  },
}));
