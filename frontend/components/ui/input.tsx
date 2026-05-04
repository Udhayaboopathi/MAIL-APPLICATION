import type { InputHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={cn(
        "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none placeholder:text-slate-400 focus:border-accent/70 focus:ring-2 focus:ring-accent/10",
        props.className,
      )}
    />
  );
}
