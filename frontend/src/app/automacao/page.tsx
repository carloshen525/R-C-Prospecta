"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import {
  Zap,
  Play,
  Pause,
  Save,
  RotateCcw,
  Sparkles,
  Globe,
  Copy,
  Check,
  SendHorizontal,
  Clock,
  Users,
  CheckCircle2,
  AlertCircle,
  Trash2,
  ExternalLink,
  ChevronRight,
  Sliders,
  FileText,
  Activity,
  History as HistoryIcon,
  ListOrdered,
  Loader2,
  Building2,
  Phone,
  MapPin,
  Eye,
  X
} from "lucide-react";
import { api } from "@/lib/api";

export default function AutomacaoPage() {
  // Estado global do status da automação
  const [status, setStatus] = useState<string>("ativa");
  const [isWindowOpen, setIsWindowOpen] = useState<boolean>(true);
  const [windowMessage, setWindowMessage] = useState<string>("");
  const [dailySent, setDailySent] = useState<number>(0);
  const [dailyLimit, setDailyLimit] = useState<number>(20);
  const [loadingStatus, setLoadingStatus] = useState<boolean>(true);

  // Prompt states
  const [prompt, setPrompt] = useState<string>("");
  const [savingPrompt, setSavingPrompt] = useState<boolean>(false);
  const [resettingPrompt, setResettingPrompt] = useState<boolean>(false);

  // Simulation states
  const [simCompany, setSimCompany] = useState<string>("Carvalho Odontologia");
  const [simWebsite, setSimWebsite] = useState<string>("https://carvalhoodontologia.com.br");
  const [simContact, setSimContact] = useState<string>("Dr. André");
  const [simCity, setSimCity] = useState<string>("Ribeirão Preto - SP");
  const [simNotes, setSimNotes] = useState<string>("Foco em implantes e estética dental");
  const [simulating, setSimulating] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Settings states
  const [settings, setSettings] = useState<any>({
    min_interval_sec: 180,
    max_interval_sec: 360,
    start_time: "07:00",
    end_time: "18:30",
    allowed_days: ["seg", "ter", "qua", "qui", "sex"],
    max_contacts_hour: 10,
    max_contacts_day: 20,
    ai_provider: "groq",
    ai_model: "qwen/qwen3.8-27b",
    temperature: 0.7,
    max_tokens: 800,
  });
  const [savingSettings, setSavingSettings] = useState<boolean>(false);

  // Metrics states
  const [stats, setStats] = useState<any>(null);

  // Queue & History states
  const [queue, setQueue] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [dispatchingNow, setDispatchingNow] = useState<boolean>(false);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState<any>(null);

  // Tabs de navegação interna
  const [activeTab, setActiveTab] = useState<"painel" | "prompt" | "simulacao" | "config" | "fila" | "historico">("painel");

  async function loadAllData() {
    try {
      const [statusRes, promptRes, settingsRes, statsRes, queueRes, historyRes] = await Promise.all([
        api.getAutomationStatus(),
        api.getAutomationPrompt(),
        api.getAutomationSettings(),
        api.getAutomationStats(),
        api.getAutomationQueue(),
        api.getAutomationHistory(),
      ]);

      if (statusRes) {
        setStatus(statusRes.status);
        setIsWindowOpen(statusRes.is_window_open);
        setWindowMessage(statusRes.window_message);
        setDailySent(statusRes.sent_today);
        setDailyLimit(statusRes.daily_limit);
      }
      if (promptRes) {
        setPrompt(promptRes.prompt);
      }
      if (settingsRes) {
        setSettings(settingsRes);
      }
      if (statsRes) {
        setStats(statsRes);
      }
      if (queueRes) {
        setQueue(queueRes.items || []);
      }
      if (historyRes) {
        setHistory(historyRes.items || []);
      }
    } catch (err) {
      console.error("Erro ao carregar dados da automação:", err);
    } finally {
      setLoadingStatus(false);
    }
  }

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 10000);
    return () => clearInterval(interval);
  }, []);

  async function handleToggleStatus(newStatus: "ativa" | "pausada") {
    try {
      setStatus(newStatus);
      const res = await api.toggleAutomationStatus(newStatus);
      setStatus(res.automation_status);
      loadAllData();
    } catch (err: any) {
      alert(`Erro ao alterar status: ${err.message}`);
    }
  }

  async function handleSavePrompt() {
    setSavingPrompt(true);
    try {
      await api.updateAutomationPrompt(prompt);
      alert("Prompt da IA atualizado e salvo com sucesso!");
    } catch (err: any) {
      alert(`Erro ao salvar prompt: ${err.message}`);
    } finally {
      setSavingPrompt(false);
    }
  }

  async function handleResetPrompt() {
    if (!confirm("Deseja restaurar o prompt padrão de fábrica? As customizações atuais serão substituídas.")) return;
    setResettingPrompt(true);
    try {
      const res = await api.resetAutomationPrompt();
      setPrompt(res.prompt);
      alert(res.message);
    } catch (err: any) {
      alert(`Erro ao restaurar prompt: ${err.message}`);
    } finally {
      setResettingPrompt(false);
    }
  }

  async function handleRunSimulation() {
    if (!simCompany.trim()) {
      alert("Por favor, informe o nome da empresa para simular.");
      return;
    }
    setSimulating(true);
    setSimulationResult(null);
    try {
      const res = await api.simulateMessage({
        company_name: simCompany,
        website_url: simWebsite || undefined,
        contact_name: simContact || undefined,
        city: simCity || undefined,
        notes: simNotes || undefined,
        custom_prompt: prompt || undefined,
      });
      setSimulationResult(res);
    } catch (err: any) {
      alert(`Erro ao gerar simulação: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  }

  async function handleSaveSettings(e: React.FormEvent) {
    e.preventDefault();
    setSavingSettings(true);
    try {
      await api.updateAutomationSettings(settings);
      alert("Configurações da automação atualizadas com sucesso!");
      loadAllData();
    } catch (err: any) {
      alert(`Erro ao salvar configurações: ${err.message}`);
    } finally {
      setSavingSettings(false);
    }
  }

  async function handleDispatchNow() {
    setDispatchingNow(true);
    try {
      const res = await api.dispatchAutomationNow();
      alert(res.message);
      loadAllData();
    } catch (err: any) {
      alert(`Erro no disparo da fila: ${err.message}`);
    } finally {
      setDispatchingNow(false);
    }
  }

  async function handleRemoveFromQueue(leadId: number) {
    if (!confirm("Remover este lead da fila de automação? Ele não será mais contatado.")) return;
    try {
      await api.removeLeadFromQueue(leadId);
      loadAllData();
    } catch (err: any) {
      alert(`Erro: ${err.message}`);
    }
  }

  function copyToClipboard(text: string, index: number) {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  }

  const isAtiva = status.toLowerCase() === "ativa";

  return (
    <>
      <Header
        title="Automação de Prospecção"
        description="Motor autônomo e contínuo de prospecção comercial via WhatsApp com Inteligência Artificial"
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={handleDispatchNow}
              disabled={dispatchingNow || !isAtiva}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition-colors shadow-xs disabled:opacity-50"
            >
              {dispatchingNow ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <SendHorizontal className="w-3.5 h-3.5" />
              )}
              Disparar Próximos da Fila
            </button>
          </div>
        }
      />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        {/* CARD PRINCIPAL DE STATUS E CONTROLE INSTANTÂNEO */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
                isAtiva ? "bg-emerald-50 text-emerald-600 border border-emerald-200" : "bg-red-50 text-red-600 border border-red-200"
              }`}
            >
              {isAtiva ? <Zap className="w-6 h-6 animate-pulse" /> : <Pause className="w-6 h-6" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-600 font-medium uppercase tracking-wider">Status da Automação</span>
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    isAtiva ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${isAtiva ? "bg-emerald-600 animate-ping" : "bg-red-600"}`} />
                  {isAtiva ? "🟢 Ativa (Processando Fila)" : "🔴 Pausada (Nenhum envio)"}
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {isAtiva
                  ? "A automação está ativa. Todo novo lead cadastrado entra na fila e recebe a sequência personalizada de 3 mensagens."
                  : "A automação está pausada. Novos leads serão enfileirados, mas nenhum disparo será realizado até que você reative."}
              </p>
              <div className="flex items-center gap-4 mt-2 text-[11px] text-slate-600">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-600" />
                  Janela: <strong>07:00 às 18:30</strong> (Segunda a Sexta • {isWindowOpen ? "Aberta" : "Fechada"})
                </span>
                <span>•</span>
                <span>
                  Disparos hoje: <strong>{dailySent}</strong> / {dailyLimit} (Máximo 20 leads/dia)
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end md:self-center">
            {isAtiva ? (
              <button
                onClick={() => handleToggleStatus("pausada")}
                className="px-4 py-2.5 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all shadow-xs"
              >
                <Pause className="w-4 h-4 text-red-600" />
                Pausar Automação
              </button>
            ) : (
              <button
                onClick={() => handleToggleStatus("ativa")}
                className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-all shadow-xs"
              >
                <Play className="w-4 h-4 text-white" />
                Iniciar Automação
              </button>
            )}
          </div>
        </div>

        {/* NAVEGAÇÃO INTERNA ENTRE ABAS */}
        <div className="border-b border-slate-200 flex items-center gap-1">
          <button
            onClick={() => setActiveTab("painel")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "painel"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            <Activity className="w-3.5 h-3.5" /> Visão Geral & Métricas
          </button>
          <button
            onClick={() => setActiveTab("simulacao")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "simulacao"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" /> Simular Mensagem
          </button>
          <button
            onClick={() => setActiveTab("prompt")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "prompt"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            <FileText className="w-3.5 h-3.5" /> Prompt da IA
          </button>
          <button
            onClick={() => setActiveTab("fila")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "fila"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            <ListOrdered className="w-3.5 h-3.5" /> Fila ({queue.length})
          </button>
          <button
            onClick={() => setActiveTab("historico")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "historico"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            <HistoryIcon className="w-3.5 h-3.5" /> Histórico ({history.length})
          </button>
          <button
            onClick={() => setActiveTab("config")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "config"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" /> Configurações Globais
          </button>
        </div>

        {/* ABA 1: VISÃO GERAL & MÉTRICAS EM TEMPO REAL */}
        {activeTab === "painel" && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
                <span className="text-[11px] text-slate-600 block">Leads na Fila</span>
                <span className="text-2xl font-bold text-slate-900 mt-1 block">{stats?.queue_count || 0}</span>
                <span className="text-[10px] text-slate-600 mt-0.5 block">Aguardando disparo</span>
              </div>
              <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
                <span className="text-[11px] text-slate-600 block">Enviadas Hoje</span>
                <span className="text-2xl font-bold text-emerald-600 mt-1 block">{stats?.sent_today || 0}</span>
                <span className="text-[10px] text-slate-600 mt-0.5 block">Limite diário: {dailyLimit}</span>
              </div>
              <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
                <span className="text-[11px] text-slate-600 block">Total de Envios</span>
                <span className="text-2xl font-bold text-slate-900 mt-1 block">{stats?.sent_total || 0}</span>
                <span className="text-[10px] text-slate-600 mt-0.5 block">Desde a criação</span>
              </div>
              <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
                <span className="text-[11px] text-slate-600 block">Leads Processados</span>
                <span className="text-2xl font-bold text-blue-600 mt-1 block">{stats?.processed_count || 0}</span>
                <span className="text-[10px] text-slate-600 mt-0.5 block">Sequências completas</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Mini Tabela: Próximos da Fila */}
              <div className="md:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <h3 className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                    <ListOrdered className="w-4 h-4 text-emerald-600" /> Próximos Estabelecimentos na Fila
                  </h3>
                  <button
                    onClick={() => setActiveTab("fila")}
                    className="text-[11px] text-emerald-600 hover:text-emerald-700 font-medium flex items-center gap-0.5"
                  >
                    Ver fila completa ({queue.length}) <ChevronRight className="w-3 h-3" />
                  </button>
                </div>

                {queue.length === 0 ? (
                  <div className="py-8 text-center text-xs text-slate-600">
                    A fila está vazia no momento. Extraia ou adicione novos leads para que entrem automaticamente na prospecção.
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {queue.slice(0, 5).map((item) => (
                      <div key={item.id} className="py-2.5 flex items-center justify-between text-xs">
                        <div>
                          <span className="font-semibold text-slate-900 block">{item.company_name}</span>
                          <span className="text-[11px] text-slate-600">
                            {item.city || "Brasil"} • {item.phone || "Sem telefone"}
                          </span>
                        </div>
                        <span className="text-[11px] bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full font-medium">
                          Na fila ({item.waiting_minutes}m)
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Informações do Motor */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
                <h3 className="text-xs font-semibold text-slate-900 pb-2 border-b border-slate-100 flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-amber-500" /> Parâmetros de Execução
                </h3>

                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between text-slate-600">
                    <span>Modo de Operação:</span>
                    <strong className="text-slate-900">Automação Contínua</strong>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Intervalo entre contatos:</span>
                    <strong className="text-slate-900">{settings.min_interval_sec}s a {settings.max_interval_sec}s</strong>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Provedor de IA:</span>
                    <strong className="text-slate-900 capitalize">{settings.ai_provider}</strong>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Modelo:</span>
                    <strong className="text-slate-900 font-mono text-[11px]">{settings.ai_model}</strong>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Estrutura do Envio:</span>
                    <strong className="text-emerald-700">Sequência de 3 mensagens</strong>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Tempo médio por lead:</span>
                    <strong className="text-slate-900">{stats?.avg_time_per_lead || "3 min"}</strong>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-100 flex gap-2">
                  <button
                    onClick={() => setActiveTab("simulacao")}
                    className="w-full py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold text-center transition-colors"
                  >
                    Testar Prompt com IA
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ABA 2: SIMULAR MENSAGEM */}
        {activeTab === "simulacao" && (
          <div className="space-y-6 max-w-4xl">
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-600" /> Simulação de Mensagem com IA
                </h3>
                <p className="text-xs text-slate-600 mt-1">
                  Valide a qualidade, naturalidade e personalização das mensagens antes de disparar para os leads reais. O sistema analisa o site, compreende o negócio e aplica rigorosamente o prompt ativo.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Nome da Empresa *</label>
                  <input
                    type="text"
                    value={simCompany}
                    onChange={(e) => setSimCompany(e.target.value)}
                    placeholder="Ex: Carvalho Odontologia"
                    className="w-full p-2.5 border border-slate-200 rounded-lg text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Site da Empresa (URL)</label>
                  <input
                    type="text"
                    value={simWebsite}
                    onChange={(e) => setSimWebsite(e.target.value)}
                    placeholder="https://exemplo.com.br"
                    className="w-full p-2.5 border border-slate-200 rounded-lg text-xs text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Nome do Responsável (Opcional)</label>
                  <input
                    type="text"
                    value={simContact}
                    onChange={(e) => setSimContact(e.target.value)}
                    placeholder="Ex: Dr. André ou Carlos"
                    className="w-full p-2.5 border border-slate-200 rounded-lg text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Cidade (Opcional)</label>
                  <input
                    type="text"
                    value={simCity}
                    onChange={(e) => setSimCity(e.target.value)}
                    placeholder="Ex: Ribeirão Preto - SP"
                    className="w-full p-2.5 border border-slate-200 rounded-lg text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-slate-700 mb-1">Observações Adicionais (Opcional)</label>
                  <input
                    type="text"
                    value={simNotes}
                    onChange={(e) => setSimNotes(e.target.value)}
                    placeholder="Ex: Foco em implantes dentários e próteses"
                    className="w-full p-2.5 border border-slate-200 rounded-lg text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  onClick={handleRunSimulation}
                  disabled={simulating || !simCompany.trim()}
                  className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-all shadow-xs disabled:opacity-50"
                >
                  {simulating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  {simulating ? "Analisando Site e Gerando..." : "Gerar Simulação"}
                </button>
              </div>
            </div>

            {/* RESULTADO DA SIMULAÇÃO */}
            {simulationResult && (
              <div className="space-y-4 animate-fadeIn">
                {/* 1. Informações Encontradas */}
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
                  <h4 className="text-xs font-semibold text-slate-900 flex items-center gap-1.5 pb-2 border-b border-slate-100">
                    <Globe className="w-4 h-4 text-emerald-600" /> Informações Encontradas no Site
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                    <div>
                      <span className="text-slate-600 block text-[11px]">Empresa:</span>
                      <strong className="text-slate-900">{simulationResult.extracted_info?.empresa}</strong>
                    </div>
                    <div>
                      <span className="text-slate-600 block text-[11px]">Segmento:</span>
                      <strong className="text-slate-900">{simulationResult.extracted_info?.segmento || "Odontologia / Saúde"}</strong>
                    </div>
                    <div>
                      <span className="text-slate-600 block text-[11px]">Cidade:</span>
                      <strong className="text-slate-900">{simulationResult.extracted_info?.cidade}</strong>
                    </div>
                    <div className="col-span-2 md:col-span-3">
                      <span className="text-slate-600 block text-[11px]">Resumo do Site:</span>
                      <p className="text-slate-800 text-[11px] mt-0.5 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        {simulationResult.extracted_info?.resumo_site}
                      </p>
                    </div>
                    {simulationResult.extracted_info?.servicos_encontrados?.length > 0 && (
                      <div className="col-span-2 md:col-span-3">
                        <span className="text-slate-600 block text-[11px] mb-1">Serviços Identificados:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {simulationResult.extracted_info.servicos_encontrados.map((srv: string, i: number) => (
                            <span key={i} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 text-[10px] rounded-md font-medium border border-indigo-100">
                              {srv}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* 2. Mensagens Geradas */}
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <div>
                      <h4 className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Mensagem Gerada pela IA
                      </h4>
                      <span className="text-[10px] text-slate-600">
                        Modelo: <strong>{simulationResult.model_used}</strong> ({simulationResult.provider_used})
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => copyToClipboard(simulationResult.full_text, 999)}
                        className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
                      >
                        {copiedIndex === 999 ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                        {copiedIndex === 999 ? "Copiado!" : "Copiar Todas"}
                      </button>
                      <button
                        onClick={handleRunSimulation}
                        disabled={simulating}
                        className="px-2.5 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
                      >
                        <RotateCcw className="w-3.5 h-3.5" /> Gerar Novamente
                      </button>
                    </div>
                  </div>

                  {/* Exibição em formato balões do WhatsApp */}
                  <div className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-100 max-w-xl">
                    {simulationResult.messages?.map((msg: any, idx: number) => (
                      <div key={idx} className="bg-emerald-600 text-white p-3.5 rounded-xl rounded-br-none shadow-xs text-xs space-y-1 relative group">
                        <div className="flex justify-between items-center text-[10px] text-emerald-100 mb-1 border-b border-emerald-500/40 pb-1">
                          <span className="font-semibold uppercase tracking-wider">Parte {msg.part}</span>
                          <button
                            onClick={() => copyToClipboard(msg.message, idx)}
                            className="hover:text-white flex items-center gap-0.5"
                          >
                            {copiedIndex === idx ? <Check className="w-3 h-3 text-emerald-200" /> : <Copy className="w-3 h-3" />}
                            {copiedIndex === idx ? "Copiado" : "Copiar"}
                          </button>
                        </div>
                        <p className="leading-relaxed whitespace-pre-wrap">{msg.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ABA 3: PROMPT DA IA */}
        {activeTab === "prompt" && (
          <div className="space-y-4 max-w-4xl bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-emerald-600" /> Editor do Prompt Mestre da IA
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  Este prompt é enviado ao LLM sempre que uma nova sequência é gerada para um lead na automação.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleResetPrompt}
                  disabled={resettingPrompt}
                  className="px-3 py-1.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Restaurar Padrão
                </button>
                <button
                  type="button"
                  onClick={handleSavePrompt}
                  disabled={savingPrompt}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
                >
                  {savingPrompt ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                  Salvar Prompt
                </button>
              </div>
            </div>

            <textarea
              rows={16}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full p-4 border border-slate-200 rounded-xl text-xs font-mono text-slate-900 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 leading-relaxed"
              placeholder="Digite as instruções e regras para a IA redigir as mensagens..."
            />

            <div className="text-[11px] text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                <strong>Dica:</strong> Após salvar o prompt, acesse a aba <strong>Simular Mensagem</strong> para testá-lo com dados reais de qualquer empresa antes de ativar os disparos.
              </span>
            </div>
          </div>
        )}

        {/* ABA 4: FILA DE LEADS */}
        {activeTab === "fila" && (
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                  <ListOrdered className="w-4 h-4 text-emerald-600" /> Fila Contínua de Prospecção
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  Estabelecimentos catalogados aguardando o processamento automático da IA e envio via WhatsApp.
                </p>
              </div>
              <button
                onClick={handleDispatchNow}
                disabled={dispatchingNow || !isAtiva}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors shadow-xs disabled:opacity-50"
              >
                {dispatchingNow ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                Disparar Próximos
              </button>
            </div>

            {queue.length === 0 ? (
              <div className="py-16 text-center text-xs text-slate-600">
                A fila está vazia. Novos estabelecimentos extraídos no <strong>Extrator de Leads</strong> entrarão aqui automaticamente.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-600 uppercase text-[10px] font-semibold border-b border-slate-100">
                    <tr>
                      <th className="py-3 px-4">Empresa</th>
                      <th className="py-3 px-4">Telefone</th>
                      <th className="py-3 px-4">Localização</th>
                      <th className="py-3 px-4">Data de Entrada</th>
                      <th className="py-3 px-4">Tempo na Fila</th>
                      <th className="py-3 px-4 text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {queue.map((lead) => (
                      <tr key={lead.id} className="hover:bg-slate-50/50">
                        <td className="py-3 px-4 font-semibold text-slate-900">{lead.company_name}</td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-700">{lead.phone || "—"}</td>
                        <td className="py-3 px-4 text-slate-600">{lead.city || "Brasil"}</td>
                        <td className="py-3 px-4 text-slate-600">
                          {lead.created_at ? new Date(lead.created_at).toLocaleDateString("pt-BR") : "—"}
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-100 text-slate-700 font-medium">
                            {lead.waiting_minutes} min
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleRemoveFromQueue(lead.id)}
                            title="Remover da fila"
                            className="p-1.5 text-slate-600 hover:text-red-600 rounded-md transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ABA 5: HISTÓRICO DE DISPAROS */}
        {activeTab === "historico" && (
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="p-5 border-b border-slate-100">
              <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                <HistoryIcon className="w-4 h-4 text-slate-700" /> Histórico de Processamento
              </h3>
              <p className="text-xs text-slate-600 mt-0.5">
                Registro de todos os contatos processados pela automação com status de entrega e mensagens enviadas.
              </p>
            </div>

            {history.length === 0 ? (
              <div className="py-16 text-center text-xs text-slate-600">Nenhum disparo registrado ainda.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-600 uppercase text-[10px] font-semibold border-b border-slate-100">
                    <tr>
                      <th className="py-3 px-4">Empresa</th>
                      <th className="py-3 px-4">Telefone</th>
                      <th className="py-3 px-4">Mensagem Gerada (Prévia)</th>
                      <th className="py-3 px-4">Horário</th>
                      <th className="py-3 px-4">Resultado</th>
                      <th className="py-3 px-4 text-right">Detalhes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {history.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50">
                        <td className="py-3 px-4 font-semibold text-slate-900">{item.company_name}</td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-700">{item.phone || "—"}</td>
                        <td className="py-3 px-4 text-slate-600 max-w-xs truncate">{item.preview_message}</td>
                        <td className="py-3 px-4 text-slate-600">
                          {item.processed_at ? new Date(item.processed_at).toLocaleString("pt-BR") : "—"}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              item.result === "sucesso"
                                ? "bg-emerald-100 text-emerald-800"
                                : item.result === "erro"
                                ? "bg-red-100 text-red-800"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {item.result === "sucesso" ? "Sucesso" : item.result === "erro" ? "Erro" : "Ignorado"}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => setSelectedHistoryItem(item)}
                            className="text-xs text-emerald-600 hover:text-emerald-700 font-medium inline-flex items-center gap-1"
                          >
                            <Eye className="w-3.5 h-3.5" /> Ver Mensagens
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ABA 6: CONFIGURAÇÕES DA AUTOMAÇÃO */}
        {activeTab === "config" && (
          <form onSubmit={handleSaveSettings} className="space-y-6 max-w-4xl bg-white border border-slate-200 rounded-xl p-6 shadow-xs text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-emerald-600" /> Parâmetros de Disparo e Conformidade
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  Regras globais de intervalo, horários permitidos e modelo de IA para toda a automação.
                </p>
              </div>
              <button
                type="submit"
                disabled={savingSettings}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
              >
                {savingSettings ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                Salvar Configurações
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block font-medium text-slate-700 mb-1">Tempo Mínimo entre Mensagens (segundos)</label>
                <input
                  type="number"
                  value={settings.min_interval_sec}
                  onChange={(e) => setSettings({ ...settings, min_interval_sec: Number(e.target.value) })}
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Tempo Máximo entre Mensagens (segundos)</label>
                <input
                  type="number"
                  value={settings.max_interval_sec}
                  onChange={(e) => setSettings({ ...settings, max_interval_sec: Number(e.target.value) })}
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Horário Inicial de Funcionamento</label>
                <input
                  type="time"
                  value={settings.start_time}
                  onChange={(e) => setSettings({ ...settings, start_time: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Horário Final de Funcionamento</label>
                <input
                  type="time"
                  value={settings.end_time}
                  onChange={(e) => setSettings({ ...settings, end_time: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Limite Máximo de Contatos por Dia</label>
                <input
                  type="number"
                  max={20}
                  value={settings.max_contacts_day}
                  onChange={(e) => setSettings({ ...settings, max_contacts_day: Math.min(20, Number(e.target.value)) })}
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
                />
                <span className="text-[10px] text-slate-600 block mt-0.5">Teto obrigatório de segurança anti-bloqueio: no máximo 20 leads/dia (Sábado e Domingo sem disparos).</span>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Provedor de IA Principal</label>
                <select
                  value={settings.ai_provider}
                  onChange={(e) => setSettings({ ...settings, ai_provider: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-lg bg-white text-slate-900"
                >
                  <option value="groq">Groq (Ultra Rápido / Recomendado)</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="openai">OpenAI</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Modelo de IA</label>
                <input
                  type="text"
                  value={settings.ai_model}
                  onChange={(e) => setSettings({ ...settings, ai_model: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900 font-mono"
                  placeholder="ex: qwen/qwen3.8-27b ou openai/gpt-oss-20b"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Temperatura de Criatividade (0.0 a 1.0)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={settings.temperature}
                  onChange={(e) => setSettings({ ...settings, temperature: Number(e.target.value) })}
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Máximo de Tokens por Resposta</label>
                <input
                  type="number"
                  value={settings.max_tokens}
                  onChange={(e) => setSettings({ ...settings, max_tokens: Number(e.target.value) })}
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
                />
              </div>
            </div>
          </form>
        )}

        {/* MODAL PARA VER MENSAGENS COMPLETAS DO HISTÓRICO */}
        {selectedHistoryItem && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fadeIn">
            <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden animate-scaleUp">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900 text-sm">{selectedHistoryItem.company_name}</h3>
                  <span className="text-[11px] text-slate-600">{selectedHistoryItem.phone}</span>
                </div>
                <button
                  onClick={() => setSelectedHistoryItem(null)}
                  className="p-1 text-slate-600 hover:text-slate-900 rounded-md"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="p-5 space-y-3 max-h-[70vh] overflow-y-auto bg-slate-50">
                {selectedHistoryItem.messages?.map((m: any, i: number) => (
                  <div key={i} className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs text-xs space-y-1">
                    <div className="flex justify-between items-center text-[10px] text-slate-600 border-b border-slate-100 pb-1">
                      <span className="font-semibold uppercase tracking-wider text-emerald-700">Parte {m.part}</span>
                      <span>{m.sent_at ? new Date(m.sent_at).toLocaleTimeString("pt-BR") : "Enviada"}</span>
                    </div>
                    <p className="text-slate-800 leading-relaxed whitespace-pre-wrap">{m.content}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
