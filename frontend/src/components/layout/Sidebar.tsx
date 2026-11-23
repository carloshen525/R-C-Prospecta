"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Search,
  Users,
  SendHorizontal,
  Bot,
  MessageSquare,
  BarChart3,
  Settings,
  LogOut,
  Clock,
  CheckCircle2,
  AlertCircle,
  Zap
} from "lucide-react";
import { api } from "@/lib/api";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Extrator de Leads", href: "/extrator", icon: Search },
  { name: "Leads", href: "/leads", icon: Users },
  { name: "Automação IA", href: "/automacao", icon: Zap },
  { name: "Inteligência Artificial", href: "/ia", icon: Bot },
  { name: "WhatsApp", href: "/whatsapp", icon: MessageSquare },
  { name: "Relatórios", href: "/relatorios", icon: BarChart3 },
  { name: "Configurações", href: "/configuracoes", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [statusInfo, setStatusInfo] = useState<{
    isOpen: boolean;
    sentToday: number;
    limit: number;
  }>({
    isOpen: true,
    sentToday: 0,
    limit: 30,
  });

  useEffect(() => {
    async function loadStatus() {
      try {
        const data = await api.getDashboard();
        if (data?.indicators) {
          setStatusInfo({
            isOpen: data.indicators.is_window_open,
            sentToday: data.indicators.contacts_sent_today,
            limit: data.indicators.daily_limit,
          });
        }
      } catch {
        // Modo offline / inicial
      }
    }
    loadStatus();
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen fixed left-0 top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-100 gap-3">
        <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
          P
        </div>
        <div>
          <span className="font-semibold text-slate-900 tracking-tight text-base">
            Prospect <span className="text-emerald-600">AI</span>
          </span>
          <span className="block text-[10px] text-slate-600 font-medium tracking-wide uppercase">
            Automação Comercial
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-emerald-50 text-emerald-800"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-emerald-600" : "text-slate-600"}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* System Status & Daily Limit Card */}
      <div className="p-3 mx-3 mb-2 rounded-xl bg-slate-50 border border-slate-200/80 text-xs">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-slate-700 font-medium flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-600" />
            Horário de Envio
          </span>
          <span
            className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold ${
              statusInfo.isOpen
                ? "bg-emerald-100 text-emerald-800"
                : "bg-amber-100 text-amber-800"
            }`}
          >
            {statusInfo.isOpen ? "07:00 - 18:30" : "Pausa"}
          </span>
        </div>

        <div className="flex items-center justify-between text-slate-700 pt-1 border-t border-slate-200/60">
          <span>Limite Diário:</span>
          <span className="font-semibold text-slate-900">
            {statusInfo.sentToday} / {statusInfo.limit}
          </span>
        </div>
        <div className="w-full bg-slate-200 h-1.5 rounded-full mt-1.5 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              statusInfo.sentToday >= statusInfo.limit ? "bg-amber-500" : "bg-emerald-600"
            }`}
            style={{ width: `${Math.min(100, (statusInfo.sentToday / statusInfo.limit) * 100)}%` }}
          />
        </div>
      </div>

      {/* User Footer */}
      <div className="p-3 border-t border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 font-semibold text-xs">
            C
          </div>
          <div className="truncate">
            <p className="text-xs font-semibold text-slate-800 truncate">Carlos</p>
            <p className="text-[11px] text-slate-600 truncate">Proprietário</p>
          </div>
        </div>
        <button
          onClick={() => {
            if (typeof window !== "undefined") {
              localStorage.removeItem("prospect_token");
              window.location.reload();
            }
          }}
          title="Sair"
          className="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
