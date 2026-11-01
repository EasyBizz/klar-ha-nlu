import { cn } from "cn";
import mark from "../../../docs/klar-mark.png";

export function KlarBrand({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)} aria-label="Klar NLU, Czech Custom Edition, Local Fork">
      <img src={mark} alt="" className="h-9 w-9 shrink-0 object-contain" />
      <span className="inline-flex min-w-0 flex-col gap-1">
        <span className="brand">Klar!</span>
        <span className="text-[0.6rem] font-medium leading-none tracking-normal text-muted-foreground">Czech Custom Edition / Local Fork</span>
      </span>
    </span>
  );
}
