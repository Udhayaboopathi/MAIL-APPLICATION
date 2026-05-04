import type { ButtonHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

export function Button({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-xl bg-accent px-4 py-2 font-semibold text-white transition hover:opacity-90",
        className,
      )}
      {...props}
    />
  );
}
