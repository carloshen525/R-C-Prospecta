"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import {
  Users,
  Send,
  MessageSquare,
  Sparkles,
  TrendingUp,
  Clock,
  Layers,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Plus
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  async function loadDashboard() {
    setLoading(true);
    try {
      const res = await api.getDashboard();
      setData(res);
    } catch (err) {
      console.error("Erro ao carregar dashboard:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const ind = data?.indicators || {
    total_leads: 0,
    leads_extracted: 0,
    leads_available: 0,
    contacts_sent_today: 0,
    daily_limit: 30,
    remaining_today: 30,
    total_messages_sent: 0,
    total_replies: 0,
    total_interested: 0,
    active_campaigns: 0,
    is_window_open: true,
    window_status_message: "Carregando...",
  };

  return (
    <>
      <Header
        title="Dashboard"
        description="Visão geral e monitoramento em tempo real da operação comercial"
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={loadDashboard}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-slate-600 ${loading ? "animate-spin" : ""}`} />
              Atualizar
            </button>
            <Link
              href="/extrator"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 text-xs font-medium text-white hover:bg-emerald-700 transition-colors shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              Nova Prospecção
            </Link>
          </div>
        }
      />

      <main className="p-8 space-y-8 flex-1 overflow-y-auto">
        {/* Banner de Status Operacional */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                ind.is_window_open ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"
              }`}
            >
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900 text-sm">
                  {ind.is_window_open ? "Janela de Envio Aberta" : "Pausa Obrigatória Ativa"}
                </span>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                    ind.is_window_open
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {ind.is_window_open ? "07:00 às 18:30" : "Retomada às 07:00"}
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-0.5">
                Fuso horário: America/Sao_Paulo • Controle atômico com limite global de {ind.daily_limit} contatos/dia.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-sm border-t md:border-t-0 md:border-l border-slate-100 pt-3 md:pt-0 md:pl-6 w-full md:w-auto">
            <div>
              <span className="block text-xs text-slate-600">Enviados hoje</span>
              <span className="text-lg font-bold text-slate-900">
                {ind.contacts_sent_today}{" "}
                <span className="text-xs font-normal text-slate-600">/ {ind.daily_limit}</span>
              </span>
            </div>
            <div>
              <span className="block text-xs text-slate-600">Vagas restantes</span>
              <span className="text-lg font-bold text-emerald-600">{ind.remaining_today}</span>
            </div>
            <div>
              <span className="block text-xs text-slate-600">Automação IA</span>
              <Link href="/automacao" className="text-lg font-bold text-emerald-600 hover:underline flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Ativa
              </Link>
            </div>
          </div>
        </div>

        {/* Indicadores Principais em Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-600 uppercase tracking-wider">Total de Leads</span>
              <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center text-slate-600">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold text-slate-900 tracking-tight">{ind.total_leads}</span>
              <p className="text-xs text-slate-600 mt-1">
                {ind.leads_available} leads disponíveis para contato
              </p>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-600 uppercase tracking-wider">Mensagens Enviadas</span>
              <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
                <Send className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold text-slate-900 tracking-tight">{ind.total_messages_sent}</span>
              <p className="text-xs text-slate-600 mt-1">
                {ind.contacts_sent_today} disparos realizados hoje
              </p>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-600 uppercase tracking-wider">Respostas Recebidas</span>
              <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                <MessageSquare className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold text-slate-900 tracking-tight">{ind.total_replies}</span>
              <p className="text-xs text-slate-600 mt-1">
                {ind.total_leads > 0
                  ? `${Math.round((ind.total_replies / Math.max(ind.total_messages_sent, 1)) * 100)}% de taxa de retorno`
                  : "Nenhum retorno ainda"}
              </p>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-600 uppercase tracking-wider">Contatos Interessados</span>
              <div className="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center text-purple-600">
                <Sparkles className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold text-emerald-600 tracking-tight">{ind.total_interested}</span>
              <p className="text-xs text-slate-600 mt-1">
                Oportunidades quentes identificadas
              </p>
            </div>
          </div>
        </div>

        {/* Gráficos e Distribuição */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Gráfico de barras simples: Atividade dos últimos 7 dias */}
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Envios e Respostas por Dia</h3>
                <p className="text-xs text-slate-600 mt-0.5">Histórico real dos últimos 7 dias</p>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5 text-slate-600">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block" /> Envios
                </span>
                <span className="flex items-center gap-1.5 text-slate-600">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-600 inline-block" /> Respostas
                </span>
              </div>
            </div>

            <div className="h-48 flex items-end justify-between gap-3 pt-6 border-b border-slate-100">
              {(data?.chart_daily_activity || []).map((day: any, idx: number) => {
                const maxVal = Math.max(1, ...data.chart_daily_activity.map((d: any) => Math.max(d.sent, d.replies)));
                const sentHeight = (day.sent / maxVal) * 100;
                const replyHeight = (day.replies / maxVal) * 100;

                return (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
                    <div className="w-full flex items-end justify-center gap-1 h-36">
                      <div
                        title={`Envios: ${day.sent}`}
                        style={{ height: `${Math.max(sentHeight, 4)}%` }}
                        className="w-1/2 bg-emerald-500 hover:bg-emerald-600 rounded-t-sm transition-all"
                      />
                      <div
                        title={`Respostas: ${day.replies}`}
                        style={{ height: `${Math.max(replyHeight, day.replies > 0 ? 4 : 0)}%` }}
                        className="w-1/2 bg-blue-500 hover:bg-blue-600 rounded-t-sm transition-all"
                      />
                    </div>
                    <span className="text-[11px] font-medium text-slate-600">{day.date}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Distribuição por Segmento */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Leads por Segmento</h3>
              <p className="text-xs text-slate-600 mt-0.5">Top nichos cadastrados na base</p>

              <div className="mt-6 space-y-4">
                {(data?.chart_segments || []).length === 0 ? (
                  <p className="text-xs text-slate-600 text-center py-8">Nenhum lead cadastrado ainda.</p>
                ) : (
                  data.chart_segments.map((seg: any, idx: number) => {
                    const total = ind.total_leads || 1;
                    const pct = Math.round((seg.count / total) * 100);
                    return (
                      <div key={idx}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="font-medium text-slate-700 truncate max-w-[180px]">{seg.segment}</span>
                          <span className="text-slate-600 font-semibold">{seg.count} ({pct}%)</span>
                        </div>
                        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-emerald-600 h-full rounded-full"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <Link
              href="/leads"
              className="text-xs text-emerald-600 hover:text-emerald-700 font-medium inline-flex items-center gap-1 mt-6"
            >
              Ver todos os leads →
            </Link>
          </div>
        </div>

        {/* Atividades Recentes */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-900">Atividades Recentes do Sistema</h3>
            <span className="text-xs text-slate-600">Logs automáticos do backend</span>
          </div>

          <div className="divide-y divide-slate-100">
            {(data?.recent_activities || []).length === 0 ? (
              <div className="text-center py-8">
                <p className="text-xs text-slate-600">Nenhuma atividade registrada no momento.</p>
              </div>
            ) : (
              data.recent_activities.map((act: any) => (
                <div key={act.id} className="py-3 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                      {act.type === "message_sent" && <Send className="w-3.5 h-3.5 text-emerald-600" />}
                      {act.type === "extraction" && <Layers className="w-3.5 h-3.5 text-blue-600" />}
                      {act.type === "reply_received" && <MessageSquare className="w-3.5 h-3.5 text-purple-600" />}
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{act.title}</p>
                      <p className="text-slate-600">{act.description}</p>
                    </div>
                  </div>
                  <span className="text-slate-600 font-mono text-[11px]">{act.timestamp}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </>
  );
}
