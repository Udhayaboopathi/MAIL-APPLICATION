import { create } from "zustand";
import type { StateCreator } from "zustand";

type ComposeState = {
  open: boolean;
  draftTo: string;
  draftSubject: string;
  draftBody: string;
  selectedFolder: string;
  setComposeOpen: (open: boolean) => void;
  setDraftField: (
    field: "draftTo" | "draftSubject" | "draftBody",
    value: string,
  ) => void;
  setSelectedFolder: (folder: string) => void;
};

const uiStoreCreator: StateCreator<ComposeState> = (set) => ({
  open: false,
  draftTo: "",
  draftSubject: "",
  draftBody: "",
  selectedFolder: "inbox",
  setComposeOpen: (open) => set({ open }),
  setDraftField: (field, value) =>
    set({ [field]: value } as Pick<ComposeState, typeof field>),
  setSelectedFolder: (folder) => set({ selectedFolder: folder }),
});

export const useUiStore = create<ComposeState>()(uiStoreCreator);
