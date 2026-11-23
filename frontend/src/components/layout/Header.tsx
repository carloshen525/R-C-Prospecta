"use client";

import { Bell, Sparkles } from "lucide-react";

interface HeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function Header({ title, description, actions }: HeaderProps) {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h1 className="text-lg font-semibold text-slate-900 tracking-tight">{title}</h1>
        {description && <p className="text-xs text-slate-600 mt-0.5">{description}</p>}
      </div>

      <div className="flex items-center gap-3">
        {actions}
      </div>
    </header>
  );
}
