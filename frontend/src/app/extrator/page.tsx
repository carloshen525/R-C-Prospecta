"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import {
  Search,
  Layers,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
  Filter,
  ArrowRight,
  Database,
  Building2,
  CheckSquare,
  Square,
  ExternalLink,
  X,
  Star,
  Phone,
  Globe,
  MapPin,
  Sparkles,
  Zap
} from "lucide-react";
import { api } from "@/lib/api";

export default function ExtratorPage() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetchingJobs, setFetchingJobs] = useState(true);
  const [googlePlacesActive, setGooglePlacesActive] = useState(false);

  // Form states
  const [source, setSource] = useState<string>("google_scraper");
  const [segment, setSegment] = useState("Clínicas odontológicas");
  const [city, setCity] = useState("Ribeirão Preto");
  const [state, setState] = useState("SP");
  const [desiredQty, setDesiredQty] = useState(20);
  const [hasPhoneFilter, setHasPhoneFilter] = useState(true);
  const [hasWebsiteFilter, setHasWebsiteFilter] = useState(false);
  const [campaignId, setCampaignId] = useState<string>("");
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Curation modal states
  const [curationJob, setCurationJob] = useState<any | null>(null);
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
  const [curationCampaignId, setCurationCampaignId] = useState<string>("");
  const [importing, setImporting] = useState<boolean>(false);
  const [curationMessage, setCurationMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  async function loadData() {
    setFetchingJobs(true);
    try {
      const [campsRes, jobsRes, settingsRes] = await Promise.all([
        api.listCampaigns(),
        api.listExtractionJobs(),
        api.getSettings(),
      ]);
      setCampaigns(campsRes || []);
      setJobs(jobsRes || []);
      if (settingsRes?.google_maps) {
        setGooglePlacesActive(settingsRes.google_maps.is_configured);
      }
    } catch (err) {
      console.error("Erro ao carregar dados do extrator:", err);
    } finally {
      setFetchingJobs(false);
    }
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(async () => {
      try {
        const jobsRes = await api.listExtractionJobs();
        setJobs(jobsRes || []);
      } catch {
        // ignore
      }
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  async function handleOpenCuration(job: any) {
    try {
      const fullJob = await api.getExtractionJob(job.id);
      setCurationJob(fullJob);
      setCurationCampaignId(fullJob.campaign_id ? String(fullJob.campaign_id) : "");
      setCurationMessage(null);
      const items = fullJob.extracted_items || [];
      const pendingIndices = items
        .filter((it: any) => !it.is_imported)
        .map((it: any) => it.index);
      setSelectedIndices(pendingIndices.length > 0 ? pendingIndices : items.map((it: any) => it.index));
    } catch (err: any) {
      console.error("Erro ao carregar detalhes do job:", err);
    }
  }

  function toggleSelectAll() {
    if (!curationJob?.extracted_items) return;
    if (selectedIndices.length === curationJob.extracted_items.length) {
      setSelectedIndices([]);
    } else {
      setSelectedIndices(curationJob.extracted_items.map((it: any) => it.index));
    }
  }

  function toggleIndex(idx: number) {
    setSelectedIndices((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  }

  async function handleImportSelected() {
    if (!curationJob || selectedIndices.length === 0) return;
    setImporting(true);
    setCurationMessage(null);
    try {
      const res = await api.importExtractedLeads(curationJob.id, {
        selected_indices: selectedIndices,
        campaign_id: curationCampaignId ? Number(curationCampaignId) : undefined,
      });
      setCurationMessage({
        type: "success",
        text: res.message || `${res.imported_count} leads importados com sucesso!`,
      });
      const updated = await api.getExtractionJob(curationJob.id);
      setCurationJob(updated);
      loadData();
    } catch (err: any) {
      setCurationMessage({
        type: "error",
        text: err.message || "Erro ao importar leads selecionados.",
      });
    } finally {
      setImporting(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const payload: any = {
        segment,
        city,
        state,
        country: "Brasil",
        desired_qty: Number(desiredQty),
        has_phone_filter: hasPhoneFilter,
        has_website_filter: hasWebsiteFilter,
        source: source,
        auto_import: false,
      };
      if (campaignId) {
        payload.campaign_id = Number(campaignId);
      }

      await api.createExtractionJob(payload);
      setMessage({
        type: "success",
        text: "Pesquisa iniciada! Você poderá revisar e selecionar exatamente quais leads importar.",
      });
      loadData();
    } catch (err: any) {
      setMessage({
        type: "error",
        text: err.message || "Erro ao iniciar extração.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header
        title="Extrator de Leads"
        description="Aquisição e estruturação de dados de empresas locais por segmento e localização"
      />

      <main className="p-8 space-y-8 flex-1 overflow-y-auto">
        {/* Banner de Fonte Ativa */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex items-center justify-between text-xs">
          <div className="flex items-center gap-3">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold ${
                googlePlacesActive ? "bg-emerald-50 text-emerald-600" : "bg-blue-50 text-blue-600"
              }`}
            >
              {googlePlacesActive ? "G" : "OSM"}
            </div>
            <div>
              <p className="font-semibold text-slate-900">
                {googlePlacesActive
                  ? "Fonte de Dados: Google Places API (Google Maps Oficial Ativo)"
                  : "Fonte de Dados: OpenStreetMap (Público & Gratuito)"}
              </p>
              <p className="text-slate-600 text-[11px]">
                {googlePlacesActive
                  ? "Buscas oficiais com telefones comerciais, avaliações, websites e horários."
                  : "Busca pública de estabelecimentos. Para extrair telefones oficiais completos do Google Maps, adicione sua chave em Configurações."}
              </p>
            </div>
          </div>

          {!googlePlacesActive && (
            <a
              href="/configuracoes"
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-medium rounded-lg transition-colors whitespace-nowrap text-xs"
            >
              Ativar Google Places API →
            </a>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Formulário de Busca */}
          <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-6 shadow-xs h-fit">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
              <Search className="w-4 h-4 text-emerald-600" />
              <h2 className="text-sm font-semibold text-slate-900">Nova Extração de Leads</h2>
            </div>

            {message && (
              <div
                className={`p-3 rounded-lg text-xs mb-4 flex items-start gap-2 ${
                  message.type === "success"
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                    : "bg-red-50 text-red-800 border border-red-200"
                }`}
              >
                {message.type === "success" ? (
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
                )}
                <span>{message.text}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-slate-700 mb-1">
                  Motor de Extração *
                </label>
                <select
                  value={source}
                  onChange={(e) => {
                    const val = e.target.value;
                    setSource(val);
                    if (val === "google_scraper") {
                      setHasPhoneFilter(true);
                      if (desiredQty > 50) setDesiredQty(30);
                    }
                  }}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 text-slate-900 bg-white font-medium"
                >
                  <option value="google_scraper">🌐 Google Maps Scraper (Navegador Automático - Sem Chave)</option>
                  <option value="google_places">⚡ Google Places API (Google Maps Oficial)</option>
                  <option value="openstreetmap">🗺️ OpenStreetMap Livre (Base Colaborativa)</option>
                  <option value="auto">🔄 Automático (Places se configurado, senão Scraper)</option>
                </select>
                <span className="text-[10px] text-slate-500 block mt-1">
                  {source === "google_scraper" && "Abre o Chromium em background, faz scroll pelo feed do Google Maps e extrai contatos reais."}
                  {source === "google_places" && "Utiliza a API oficial do Google Cloud com ultra-velocidade e dados estruturados."}
                  {source === "openstreetmap" && "Gratuito e público. Atenção: estabelecimentos no OSM costumam vir sem telefone cadastrado."}
                  {source === "auto" && "Alterna inteligentemente entre a API oficial e o Scraper de navegador."}
                </span>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">
                  Segmento ou Palavra-chave *
                </label>
                <input
                  type="text"
                  required
                  placeholder="ex: Clínicas odontológicas"
                  value={segment}
                  onChange={(e) => setSegment(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 text-slate-900"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2">
                  <label className="block font-medium text-slate-700 mb-1">Cidade *</label>
                  <input
                    type="text"
                    required
                    placeholder="ex: Ribeirão Preto"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 text-slate-900"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-700 mb-1">UF *</label>
                  <input
                    type="text"
                    required
                    maxLength={2}
                    placeholder="SP"
                    value={state}
                    onChange={(e) => setState(e.target.value.toUpperCase())}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 text-slate-900 text-center uppercase"
                  />
                </div>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">
                  Quantidade Desejada
                </label>
                <input
                  type="number"
                  min={5}
                  max={200}
                  value={desiredQty}
                  onChange={(e) => setDesiredQty(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 text-slate-900"
                />
                <span className="text-[10px] text-slate-600 block mt-0.5">
                  Recomendado: 50 a 100 por extração
                </span>
              </div>

              <div className="bg-emerald-50/60 p-3 rounded-lg border border-emerald-100 text-xs">
                <span className="font-semibold text-emerald-900 block flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-emerald-600" /> Fila Automática de Prospecção
                </span>
                <span className="text-emerald-700 text-[11px] block mt-0.5">
                  Todos os leads aprovados entram automaticamente na fila contínua da Automação de Prospecção.
                </span>
              </div>

              {/* Filtros de Validação Pré-salvamento */}
              <div className="pt-2 border-t border-slate-100 space-y-2">
                <span className="font-medium text-slate-700 block">Critérios de Qualidade</span>
                <label className="flex items-start gap-2 cursor-pointer text-slate-600">
                  <input
                    type="checkbox"
                    checked={hasPhoneFilter}
                    onChange={(e) => setHasPhoneFilter(e.target.checked)}
                    className="rounded text-emerald-600 focus:ring-emerald-500 w-3.5 h-3.5 mt-0.5"
                  />
                  <div>
                    <span>Apenas estabelecimentos com telefone cadastrado</span>
                    <span className="block text-[10px] text-slate-600 mt-0.5">
                      No OpenStreetMap gratuito, muitos nós não têm telefone. Desmarque se o retorno for 0 ou ative a Google Places API.
                    </span>
                  </div>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-600">
                  <input
                    type="checkbox"
                    checked={hasWebsiteFilter}
                    onChange={(e) => setHasWebsiteFilter(e.target.checked)}
                    className="rounded text-emerald-600 focus:ring-emerald-500 w-3.5 h-3.5"
                  />
                  <span>Apenas empresas com website próprio</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg shadow-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50 mt-4"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Iniciando Tarefa...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    <span>Iniciar Extração</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Histórico e Monitor de Extrações */}
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-slate-600" />
                <h2 className="text-sm font-semibold text-slate-900">Histórico de Tarefas</h2>
              </div>
              <span className="text-xs text-slate-600">Atualização em tempo real</span>
            </div>

            {fetchingJobs && jobs.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-600">Carregando tarefas...</div>
            ) : jobs.length === 0 ? (
              <div className="text-center py-12">
                <Building2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-xs font-medium text-slate-700">Nenhuma extração realizada</p>
                <p className="text-xs text-slate-600 mt-1">
                  Preencha o formulário ao lado para pesquisar estabelecimentos e alimentar sua base de leads.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Segmento / Local</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3 text-center">Encontrados</th>
                      <th className="py-2.5 px-3 text-center">Salvos</th>
                      <th className="py-2.5 px-3 text-center">Duplicados</th>
                      <th className="py-2.5 px-3 text-right">Tempo</th>
                      <th className="py-2.5 px-3 text-right">Ação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {jobs.map((j) => (
                      <tr key={j.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-slate-900">{j.segment}</p>
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                              {j.source === "google_scraper"
                                ? "Maps Scraper"
                                : j.source === "google_places"
                                ? "Places API"
                                : j.source === "openstreetmap"
                                ? "OpenStreetMap"
                                : "Auto"}
                            </span>
                          </div>
                          <p className="text-slate-600 text-[11px]">
                            {j.city} - {j.state}
                          </p>
                          {j.error_log && (
                            <p className="text-[10px] text-amber-700 bg-amber-50 p-1.5 rounded mt-1 border border-amber-200">
                              ℹ️ {j.error_log}
                            </p>
                          )}
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              j.status === "completed"
                                ? "bg-emerald-100 text-emerald-800"
                                : j.status === "running"
                                ? "bg-blue-100 text-blue-800 animate-pulse"
                                : j.status === "failed"
                                ? "bg-red-100 text-red-800"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {j.status === "completed"
                              ? "Concluído"
                              : j.status === "running"
                              ? "Processando..."
                              : j.status === "failed"
                              ? "Erro"
                              : "Pendente"}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-center font-medium text-slate-800">
                          {j.found_count}
                        </td>
                        <td className="py-3 px-3 text-center font-semibold text-emerald-600">
                          {j.saved_count}
                        </td>
                        <td className="py-3 px-3 text-center text-slate-600">
                          {j.duplicate_count}
                        </td>
                        <td className="py-3 px-3 text-right text-slate-600 font-mono">
                          {j.execution_time_seconds > 0 ? `${j.execution_time_seconds}s` : "—"}
                        </td>
                        <td className="py-3 px-3 text-right whitespace-nowrap">
                          {j.found_count > 0 ? (
                            <button
                              type="button"
                              onClick={() => handleOpenCuration(j)}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium text-xs transition-colors shadow-xs"
                            >
                              <CheckSquare className="w-3.5 h-3.5" />
                              <span>Selecionar Leads ({j.saved_count}/{j.found_count})</span>
                            </button>
                          ) : (
                            <span className="text-slate-400 text-xs">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Modal de Curadoria e Seleção de Leads */}
        {curationJob && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white border border-slate-200 rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
              {/* Header do Modal */}
              <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                <div>
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-emerald-600" />
                    <h3 className="font-semibold text-slate-900 text-sm">
                      Curadoria de Leads Extraídos — {curationJob.segment}
                    </h3>
                  </div>
                  <p className="text-slate-600 text-xs mt-0.5">
                    Localização: <span className="font-medium text-slate-700">{curationJob.city} - {curationJob.state}</span> | Origem: <span className="font-medium text-slate-700">{curationJob.source}</span>
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setCurationJob(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Mensagem de Feedback */}
              {curationMessage && (
                <div
                  className={`mx-5 mt-4 p-3 rounded-lg text-xs flex items-center gap-2 ${
                    curationMessage.type === "success"
                      ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                      : "bg-red-50 text-red-800 border border-red-200"
                  }`}
                >
                  {curationMessage.type === "success" ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                  ) : (
                    <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
                  )}
                  <span>{curationMessage.text}</span>
                </div>
              )}

              {/* Barra de Controles e Seleção */}
              <div className="p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs bg-white">
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={toggleSelectAll}
                    className="flex items-center gap-1.5 font-medium text-slate-700 hover:text-emerald-700 px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
                  >
                    {selectedIndices.length === (curationJob.extracted_items?.length || 0) && selectedIndices.length > 0 ? (
                      <>
                        <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Desmarcar Todos</span>
                      </>
                    ) : (
                      <>
                        <Square className="w-3.5 h-3.5 text-slate-400" />
                        <span>Selecionar Todos</span>
                      </>
                    )}
                  </button>
                  <span className="text-slate-600">
                    <strong className="text-slate-900">{selectedIndices.length}</strong> de{" "}
                    {curationJob.extracted_items?.length || 0} estabelecimentos selecionados
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-[11px] bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded-md font-semibold border border-emerald-200">
                    ⚡ Fila Automática de Prospecção
                  </span>

                  <button
                    type="button"
                    onClick={handleImportSelected}
                    disabled={importing || selectedIndices.length === 0}
                    className="py-1.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg text-xs transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-xs"
                  >
                    {importing ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Importando...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Importar ({selectedIndices.length}) para Leads</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Lista de Leads Extraídos */}
              <div className="flex-1 overflow-y-auto p-4 space-y-2 divide-y divide-slate-100">
                {(!curationJob.extracted_items || curationJob.extracted_items.length === 0) ? (
                  <div className="text-center py-12 text-slate-500 text-xs">
                    Nenhum estabelecimento estruturado neste lote.
                  </div>
                ) : (
                  curationJob.extracted_items.map((item: any) => {
                    const isSelected = selectedIndices.includes(item.index);
                    return (
                      <div
                        key={item.index}
                        onClick={() => toggleIndex(item.index)}
                        className={`pt-3 first:pt-0 flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-colors ${
                          isSelected ? "bg-emerald-50/50 border border-emerald-200/60" : "hover:bg-slate-50 border border-transparent"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          className="mt-1 rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 cursor-pointer"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <h4 className="font-semibold text-slate-900 text-xs truncate">
                              {item.company_name}
                            </h4>
                            <div className="flex items-center gap-2 shrink-0">
                              {item.is_imported && (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                                  ✓ Já na Base
                                </span>
                              )}
                              {item.rating && (
                                <span className="flex items-center gap-1 text-[11px] font-medium text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">
                                  <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                                  {item.rating} {item.rating_count ? `(${item.rating_count})` : ""}
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5 text-[11px] text-slate-600">
                            {item.phone ? (
                              <span className="flex items-center gap-1 text-slate-800 font-mono">
                                <Phone className="w-3 h-3 text-emerald-600" />
                                {item.phone}
                              </span>
                            ) : (
                              <span className="text-slate-400 italic">Sem telefone público</span>
                            )}

                            {item.website && (
                              <a
                                href={item.website}
                                target="_blank"
                                rel="noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="flex items-center gap-1 text-blue-600 hover:underline truncate max-w-xs"
                              >
                                <Globe className="w-3 h-3 shrink-0" />
                                <span className="truncate">{item.website}</span>
                                <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                              </a>
                            )}

                            {item.address && (
                              <span className="flex items-center gap-1 text-slate-500 truncate max-w-sm">
                                <MapPin className="w-3 h-3 shrink-0 text-slate-400" />
                                <span className="truncate">{item.address}</span>
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Rodapé do Modal */}
              <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between text-xs">
                <span className="text-slate-500">
                  Os leads selecionados serão salvos na aba <strong>Leads</strong> e vinculados à campanha.
                </span>
                <button
                  type="button"
                  onClick={() => setCurationJob(null)}
                  className="px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg font-medium transition-colors"
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
