"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function CampanhasRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/automacao");
  }, [router]);

  return (
    <div className="flex-1 flex items-center justify-center p-8 text-xs text-slate-600">
      Redirecionando para a nova Automação de Prospecção...
    </div>
  );
}
