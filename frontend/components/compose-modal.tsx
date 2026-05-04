"use client";

import { Send } from "lucide-react";

import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogTrigger } from "./ui/dialog";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { useUiStore } from "../store/ui-store";

export function ComposeModal() {
  const open = useUiStore((state) => state.open);
  const setComposeOpen = useUiStore((state) => state.setComposeOpen);
  const draftTo = useUiStore((state) => state.draftTo);
  const draftSubject = useUiStore((state) => state.draftSubject);
  const draftBody = useUiStore((state) => state.draftBody);
  const setDraftField = useUiStore((state) => state.setDraftField);

  return (
    <Dialog open={open} onOpenChange={setComposeOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Send size={16} /> Compose
        </Button>
      </DialogTrigger>
      <DialogContent>
        <div className="mb-5">
          <h2 className="font-display text-2xl font-semibold tracking-tight">
            Compose message
          </h2>
          <p className="mt-1 text-sm text-muted">
            Draft, track, and send from the transaction-safe SMTP pipeline.
          </p>
        </div>
        <div className="space-y-3">
          <Input
            placeholder="To"
            value={draftTo}
            onChange={(event) => setDraftField("draftTo", event.target.value)}
          />
          <Input
            placeholder="Subject"
            value={draftSubject}
            onChange={(event) =>
              setDraftField("draftSubject", event.target.value)
            }
          />
          <Textarea
            placeholder="Write your email..."
            value={draftBody}
            onChange={(event) => setDraftField("draftBody", event.target.value)}
          />
          <div className="flex items-center justify-between pt-2">
            <span className="text-sm text-muted">
              Rich editor can be swapped in later with TipTap or Lexical.
            </span>
            <Button>Send</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
