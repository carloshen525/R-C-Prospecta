"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import {
  Users,
  Search,
  Filter,
  Phone,
  Globe,
  Star,
  CheckCircle,
  AlertCircle,
  X,
  ExternalLink,
  MessageSquare,
  Sparkles,
  ChevronRight,
  ShieldAlert,
  Send,
  Plus
} from "lucide-react";
import { api } from "@/lib/api";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  novo: { label: "Novo", color: "bg-slate-100 text-slate-700" },
  aguardando_processamento: { label: "Aguardando", color: "bg-blue-100 text-blue-800" },
  mensagens_geradas: { label: "Mensagens Geradas", color: "bg-indigo-100 text-indigo-800" },
  na_fila: { label: "Na Fila", color: "bg-amber-100 text-amber-800" },
  contatado: { label: "Contatado", color: "bg-emerald-100 text-emerald-800" },
  respondeu: { label: "Respondeu", color: "bg-teal-100 text-teal-800" },
  interessado: { label: "Interessado", color: "bg-purple-100 text-purple-800" },
  sem_interesse: { label: "Sem Interesse", color: "bg-gray-100 text-gray-700" },
  nao_contatar: { label: "Não Contatar", color: "bg-red-100 text-red-800" },
  erro: { label: "Erro", color: "bg-red-100 text-red-800" },
};

export default function LeadsPage() {
  const [leads, setLeads] = useState<any[]>([]);
  const [totalLeads, setTotalLeads] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<any>(null);
  const [leadDetail, setLeadDetail] = useState<any>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Filtros
  const [search, setSearch] = useState("");
  const [segment, setSegment] = useState("");
  const [city, setCity] = useState("");
  const [status, setStatus] = useState("");
  const [hasPhone, setHasPhone] = useState<string>("all");
  const [hasWebsite, setHasWebsite] = useState<string>("all");

  // Ações em lote
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [bulkCampaignId, setBulkCampaignId] = useState("");

  async function loadLeads() {
    setLoading(true);
    try {
      const params: any = { search, segment, city, status, limit: 100 };
      if (hasPhone === "true") params.has_phone = true;
      if (hasPhone === "false") params.has_phone = false;
      if (hasWebsite === "true") params.has_website = true;
      if (hasWebsite === "false") params.has_website = false;

      const res = await api.listLeads(params);
      setLeads(res.items || []);
      setTotalLeads(res.total || 0);
    } catch (err) {
      console.error("Erro ao listar leads:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLeads();
    api.listCampaigns().then(setCampaigns).catch(() => {});
  }, [segment, city, status, hasPhone, hasWebsite]);

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    loadLeads();
  }

  async function handleOpenDetail(lead: any) {
    setSelectedLead(lead);
    setLoadingDetail(true);
    try {
      const res = await api.getLeadDetails(lead.id);
      setLeadDetail(res);
    } catch (err) {
      console.error("Erro ao carregar detalhes do lead:", err);
    } finally {
      setLoadingDetail(false);
    }
  }

  function toggleSelectAll() {
    if (selectedIds.length === leads.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(leads.map((l) => l.id));
    }
  }

  function toggleSelectOne(id: number) {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((x) => x !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  }

  async function executeBulkEnqueue() {
    if (selectedIds.length === 0) return;
    try {
      await api.bulkLeadAction({
        action: "update_status",
        status: "novo",
        lead_ids: selectedIds,
      });
      alert(`${selectedIds.length} lead(s) colocados na Fila de Automação com sucesso!`);
      setSelectedIds([]);
      loadLeads();
    } catch (err: any) {
      alert(`Erro: ${err.message}`);
    }
  }

  async function executeBulkBlock() {
    if (selectedIds.length === 0) return;
    if (!confirm(`Deseja bloquear ${selectedIds.length} lead(s) e adicioná-los à lista de não contatar?`)) return;
    try {
      await api.bulkLeadAction({
        action: "block",
        lead_ids: selectedIds,
      });
      setSelectedIds([]);
      loadLeads();
    } catch (err: any) {
      alert(`Erro: ${err.message}`);
    }
  }

  return (
    <>
      <Header
        title="Gerenciador de Leads"
        description={`${totalLeads} contatos comerciais catalogados`}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={loadLeads}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
            >
              Recarregar
            </button>
          </div>
        }
      />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        {/* Barra de Filtros e Busca */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3">
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-600 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Buscar por nome da empresa, telefone, cidade ou nicho..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 text-slate-900"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition-colors shadow-xs"
            >
              Buscar
            </button>
          </form>

          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 text-xs text-slate-600">
            <span className="font-medium text-slate-700 flex items-center gap-1">
              <Filter className="w-3.5 h-3.5 text-slate-600" /> Filtros:
            </span>

            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="px-2.5 py-1.5 border border-slate-200 rounded-md bg-white text-slate-700 text-xs focus:outline-none"
            >
              <option value="">Todos os status</option>
              <option value="novo">Novo</option>
              <option value="mensagens_geradas">Mensagens Geradas</option>
              <option value="contatado">Contatado</option>
              <option value="respondeu">Respondeu</option>
              <option value="interessado">Interessado</option>
              <option value="sem_interesse">Sem Interesse</option>
              <option value="nao_contatar">Não Contatar</option>
            </select>

            <select
              value={hasPhone}
              onChange={(e) => setHasPhone(e.target.value)}
              className="px-2.5 py-1.5 border border-slate-200 rounded-md bg-white text-slate-700 text-xs focus:outline-none"
            >
              <option value="all">Telefone: Todos</option>
              <option value="true">Com Telefone</option>
              <option value="false">Sem Telefone</option>
            </select>

            <select
              value={hasWebsite}
              onChange={(e) => setHasWebsite(e.target.value)}
              className="px-2.5 py-1.5 border border-slate-200 rounded-md bg-white text-slate-700 text-xs focus:outline-none"
            >
              <option value="all">Website: Todos</option>
              <option value="true">Com Website</option>
              <option value="false">Sem Website</option>
            </select>

            {(search || status || hasPhone !== "all" || hasWebsite !== "all") && (
              <button
                onClick={() => {
                  setSearch("");
                  setStatus("");
                  setHasPhone("all");
                  setHasWebsite("all");
                }}
                className="text-xs text-red-600 hover:underline ml-2"
              >
                Limpar filtros
              </button>
            )}
          </div>
        </div>

        {/* Barra de Ações em Lote */}
        {selectedIds.length > 0 && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 flex items-center justify-between text-xs animate-fadeIn">
            <span className="font-medium text-emerald-900">
              {selectedIds.length} lead(s) selecionado(s)
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={executeBulkEnqueue}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors flex items-center gap-1 shadow-xs"
              >
                ⚡ Colocar na Fila da Automação
              </button>

              <button
                onClick={executeBulkBlock}
                className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
              >
                Bloquear
              </button>
            </div>
          </div>
        )}

        {/* Tabela de Leads */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
          {loading ? (
            <div className="py-20 text-center text-xs text-slate-600">Carregando leads...</div>
          ) : leads.length === 0 ? (
            <div className="text-center py-16">
              <Users className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-xs font-medium text-slate-700">Nenhum lead encontrado com os filtros aplicados</p>
              <p className="text-xs text-slate-600 mt-1">
                Tente ajustar os critérios de pesquisa ou realize uma nova extração.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200 select-none">
                  <tr>
                    <th className="py-3 px-4 w-8">
                      <input
                        type="checkbox"
                        checked={selectedIds.length === leads.length && leads.length > 0}
                        onChange={toggleSelectAll}
                        className="rounded text-emerald-600 focus:ring-emerald-500 w-3.5 h-3.5"
                      />
                    </th>
                    <th className="py-3 px-3">Empresa</th>
                    <th className="py-3 px-3">Telefone</th>
                    <th className="py-3 px-3">Localização</th>
                    <th className="py-3 px-3">Segmento</th>
                    <th className="py-3 px-3 text-center">Website</th>
                    <th className="py-3 px-3 text-center">Avaliação</th>
                    <th className="py-3 px-3 text-center">Status</th>
                    <th className="py-3 px-3 text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {leads.map((l) => {
                    const st = STATUS_LABELS[l.status] || { label: l.status, color: "bg-slate-100 text-slate-700" };
                    const isSelected = selectedIds.includes(l.id);

                    return (
                      <tr
                        key={l.id}
                        className={`hover:bg-slate-50/80 transition-colors ${
                          isSelected ? "bg-emerald-50/40" : ""
                        }`}
                      >
                        <td className="py-3 px-4">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelectOne(l.id)}
                            className="rounded text-emerald-600 focus:ring-emerald-500 w-3.5 h-3.5"
                          />
                        </td>
                        <td className="py-3 px-3">
                          <button
                            onClick={() => handleOpenDetail(l)}
                            className="font-medium text-slate-900 hover:text-emerald-600 transition-colors text-left"
                          >
                            {l.company_name}
                          </button>
                        </td>
                        <td className="py-3 px-3 font-mono text-slate-700">
                          {l.phone || <span className="text-slate-600 font-sans italic">Sem telefone</span>}
                        </td>
                        <td className="py-3 px-3 text-slate-600">
                          {l.city} {l.state ? `- ${l.state}` : ""}
                        </td>
                        <td className="py-3 px-3 text-slate-600 truncate max-w-[140px]">
                          {l.segment || "—"}
                        </td>
                        <td className="py-3 px-3 text-center">
                          {l.website ? (
                            <a
                              href={l.website.startsWith("http") ? l.website : `https://${l.website}`}
                              target="_blank"
                              rel="noreferrer"
                              title={l.website}
                              className="text-emerald-600 hover:text-emerald-700 inline-block"
                            >
                              <Globe className="w-4 h-4" />
                            </a>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-center">
                          {l.rating ? (
                            <span className="inline-flex items-center gap-1 font-medium text-slate-800">
                              <Star className="w-3 h-3 text-amber-500 fill-amber-500" />
                              {l.rating.toFixed(1)}
                            </span>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-center">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${st.color}`}
                          >
                            {st.label}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-right">
                          <button
                            onClick={() => handleOpenDetail(l)}
                            className="p-1 hover:bg-slate-100 rounded text-slate-600 hover:text-slate-900 transition-colors"
                          >
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal / Slideover de Detalhes do Lead */}
        {selectedLead && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex justify-end animate-fadeIn">
            <div className="w-full max-w-xl bg-white h-full shadow-2xl flex flex-col overflow-hidden animate-slideLeft">
              {/* Header do Drawer */}
              <div className="p-6 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-semibold text-slate-900">
                    {selectedLead.company_name}
                  </h3>
                  <span className="text-xs text-slate-600">
                    {selectedLead.segment} • {selectedLead.city} - {selectedLead.state}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedLead(null)}
                  className="p-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Corpo do Drawer */}
              <div className="flex-1 p-6 space-y-6 overflow-y-auto text-xs">
                {/* Dados Cadastrais */}
                <div className="space-y-2 pb-4 border-b border-slate-100">
                  <h4 className="font-semibold text-slate-900 text-xs uppercase tracking-wider">
                    Informações da Empresa
                  </h4>
                  <div className="grid grid-cols-2 gap-3 text-slate-600">
                    <div>
                      <span className="block text-slate-600 font-medium">Telefone:</span>
                      <span className="font-mono text-slate-900 font-semibold">
                        {selectedLead.phone || "Não informado"}
                      </span>
                    </div>
                    <div>
                      <span className="block text-slate-600 font-medium">Website:</span>
                      {selectedLead.website ? (
                        <a
                          href={selectedLead.website.startsWith("http") ? selectedLead.website : `https://${selectedLead.website}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-emerald-600 hover:underline flex items-center gap-1 truncate"
                        >
                          {selectedLead.website} <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span className="text-slate-600">Não possui</span>
                      )}
                    </div>
                    <div>
                      <span className="block text-slate-600 font-medium">Endereço:</span>
                      <span className="text-slate-800">{selectedLead.address || "—"}</span>
                    </div>
                    <div>
                      <span className="block text-slate-600 font-medium">Fonte:</span>
                      <span className="text-slate-800">{selectedLead.source}</span>
                    </div>
                  </div>
                </div>

                {/* Análise de Inteligência do Site */}
                {leadDetail?.lead?.website_data && (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
                    <div className="flex items-center gap-1.5 text-emerald-800 font-semibold">
                      <Sparkles className="w-4 h-4 text-emerald-600" />
                      Análise Pública do Website
                    </div>
                    <p className="text-slate-700">
                      <strong>Título:</strong> {leadDetail.lead.website_data.title || "—"}
                    </p>
                    <p className="text-slate-600">
                      <strong>Sobre:</strong> {leadDetail.lead.website_data.about_summary || "Sem descrição pública adicional"}
                    </p>
                  </div>
                )}

                {/* Sequência de 3 Mensagens Geradas */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-slate-900 text-xs uppercase tracking-wider">
                      Sequência Personalizada (Carlos / Meta Ads)
                    </h4>
                    <span className="text-slate-600 font-normal">3 mensagens</span>
                  </div>

                  {loadingDetail ? (
                    <p className="text-slate-600">Carregando sequência...</p>
                  ) : !leadDetail?.messages || leadDetail.messages.length === 0 ? (
                    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-amber-800">
                      Mensagens ainda não geradas para este lead. Elas serão geradas automaticamente pelo motor da Automação de Prospecção.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {leadDetail.messages.map((m: any) => (
                        <div
                          key={m.id}
                          className="border border-slate-200 rounded-xl p-3 bg-white space-y-1.5 shadow-2xs"
                        >
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="font-semibold text-slate-800">
                              Parte {m.part_number} —{" "}
                              {m.part_number === 1
                                ? "Atenção"
                                : m.part_number === 2
                                ? "Interesse"
                                : "Apresentação e Convite"}
                            </span>
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                                m.status === "enviado"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : m.status === "cancelado"
                                  ? "bg-slate-100 text-slate-600"
                                  : "bg-blue-100 text-blue-800"
                              }`}
                            >
                              {m.status}
                            </span>
                          </div>
                          <p className="text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-100 whitespace-pre-wrap">
                            {m.final_content}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
