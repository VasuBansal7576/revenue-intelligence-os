import type { BadgeTone } from "./format";

export function Badge({ children, tone = "info" }: { readonly children: string; readonly tone?: BadgeTone }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
