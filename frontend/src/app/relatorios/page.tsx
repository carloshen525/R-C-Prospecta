"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import {
  BarChart3,
  Download,
  TrendingUp,
  Percent,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Send,
  MessageSquare,
  Sparkles
} from "lucide-react";
import { api } from "@/lib/api";

export default function RelatoriosPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  async function loadReports() {
    setLoading(true);
    try {
      const res = await api.getReports();
      setData(res);
    } catch (err) {
      console.error("Erro ao carregar relatórios:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReports();
  }, []);

  function handleExportCsv() {
    window.open(api.getExportCsvUrl(), "_blank");
  }

  return (
    <>
      <Header
        title="Relatórios e Métricas"
        description="Métricas consolidadas de conversão, engajamento e performance da operação"
        actions={
          <button
            onClick={handleExportCsv}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition-colors shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            Exportar CSV
          </button>
        }
      />

      <main className="p-8 space-y-8 flex-1 overflow-y-auto">
        {loading ? (
          <div className="py-20 text-center text-xs text-slate-600">Carregando métricas...</div>
        ) : !data ? (
          <div className="text-center py-20 text-xs text-slate-600">Nenhum dado disponível.</div>
        ) : (
          <>
            {/* Top Cards de Taxas de Conversão */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
                <span className="text-xs font-medium text-slate-600 uppercase tracking-wider">
                  Taxa de Resposta
                </span>
                <div className="mt-3 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-slate-900">{data.response_rate}%</span>
                  <span className="text-xs text-slate-600 font-medium">
                    {data.total_responses} de {data.total_contacts_sent}
                  </span>
                </div>
                <p className="text-xs text-slate-600 mt-1">Leads que retornaram o contato</p>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
                <span className="text-xs font-medium text-slate-600 uppercase tracking-wider">
                  Taxa de Interesse
                </span>
                <div className="mt-3 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-emerald-600">{data.interest_rate}%</span>
                  <span className="text-xs text-slate-600 font-medium">
                    {data.total_interested} de {data.total_responses}
                  </span>
                </div>
                <p className="text-xs text-slate-600 mt-1">Qualificados como oportunidades</p>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
                <span className="text-xs font-medium text-slate-600 uppercase tracking-wider">
                  Volume de Mensagens
                </span>
                <div className="mt-3 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-slate-900">{data.total_messages}</span>
                  <span className="text-xs text-slate-600 font-medium">Disparos</span>
                </div>
                <p className="text-xs text-slate-600 mt-1">Total de partes 1, 2 e 3 entregues</p>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
                <span className="text-xs font-medium text-slate-600 uppercase tracking-wider">
                  Falhas Registradas
                </span>
                <div className="mt-3 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-slate-900">{data.total_errors}</span>
                  <span className="text-xs text-slate-600 font-medium">Erros</span>
                </div>
                <p className="text-xs text-slate-600 mt-1">Números inválidos ou bloqueados</p>
              </div>
            </div>

            {/* Performance por Campanha */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-sm font-semibold text-slate-900">Desempenho por Campanha</h3>
                <span className="text-xs text-slate-600">Métricas comparativas</span>
              </div>

              {data.campaigns.length === 0 ? (
                <p className="text-xs text-slate-600 py-6 text-center">Nenhuma campanha para exibir.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-600 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3">Campanha</th>
                        <th className="py-2.5 px-3 text-center">Leads</th>
                        <th className="py-2.5 px-3 text-center">Disparos</th>
                        <th className="py-2.5 px-3 text-center">Respostas</th>
                        <th className="py-2.5 px-3 text-center">Taxa Resposta</th>
                        <th className="py-2.5 px-3 text-center">Interessados</th>
                        <th className="py-2.5 px-3 text-right">Taxa Interesse</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.campaigns.map((c: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="py-3 px-3 font-medium text-slate-900">{c.campaign_name}</td>
                          <td className="py-3 px-3 text-center text-slate-700">{c.leads_count}</td>
                          <td className="py-3 px-3 text-center text-slate-700">{c.sent_count}</td>
                          <td className="py-3 px-3 text-center font-semibold text-blue-600">
                            {c.reply_count}
                          </td>
                          <td className="py-3 px-3 text-center text-slate-800">{c.reply_rate}%</td>
                          <td className="py-3 px-3 text-center font-bold text-emerald-600">
                            {c.interested_count}
                          </td>
                          <td className="py-3 px-3 text-right font-semibold text-slate-900">
                            {c.interested_rate}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Performance por Segmento & Provedor de IA */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Segmentos */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-sm font-semibold text-slate-900">Conversão por Segmento</h3>
                  <span className="text-xs text-slate-600">Eficiência de abordagem</span>
                </div>

                {data.segments.length === 0 ? (
                  <p className="text-xs text-slate-600 py-6 text-center">Nenhum segmento registrado.</p>
                ) : (
                  <div className="divide-y divide-slate-100 text-xs">
                    {data.segments.map((s: any, idx: number) => (
                      <div key={idx} className="py-2.5 flex items-center justify-between">
                        <div>
                          <p className="font-medium text-slate-900">{s.segment}</p>
                          <p className="text-slate-600 text-[11px]">
                            {s.leads_count} leads • {s.sent_count} contatados
                          </p>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-slate-900">{s.reply_rate}%</span>
                          <span className="block text-[10px] text-slate-600">taxa resposta</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* IA Providers */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-sm font-semibold text-slate-900">Eficácia dos Modelos de IA</h3>
                  <span className="text-xs text-slate-600">Respostas geradas</span>
                </div>

                {data.ai_providers.length === 0 ? (
                  <p className="text-xs text-slate-600 py-6 text-center">Nenhum provedor de IA com sequências geradas ainda.</p>
                ) : (
                  <div className="divide-y divide-slate-100 text-xs">
                    {data.ai_providers.map((a: any, idx: number) => (
                      <div key={idx} className="py-2.5 flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-slate-900">{a.ai_provider}</p>
                          <p className="text-slate-600 text-[11px]">
                            {a.sequences_generated} sequências criadas
                          </p>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-emerald-600">{a.reply_rate}%</span>
                          <span className="block text-[10px] text-slate-600">taxa engajamento</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </main>
    </>
  );
}
