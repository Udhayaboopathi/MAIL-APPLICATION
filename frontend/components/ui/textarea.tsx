import type { TextareaHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={cn(
        "min-h-28 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-text outline-none placeholder:text-muted focus:border-accent/70",
        props.className,
      )}
    />
  );
}
