"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import {
  Settings,
  MessageSquare,
  Bot,
  Clock,
  ShieldAlert,
  Save,
  Zap,
  CheckCircle2,
  AlertCircle,
  Loader2
} from "lucide-react";
import { api } from "@/lib/api";

export default function ConfiguracoesPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingEvo, setTestingEvo] = useState(false);
  const [evoTestResult, setEvoTestResult] = useState<any>(null);

  // Google Maps
  const [googleKey, setGoogleKey] = useState("");
  const [testingGoogle, setTestingGoogle] = useState(false);
  const [googleTestResult, setGoogleTestResult] = useState<any>(null);
  const [googleConfigured, setGoogleConfigured] = useState(false);

  // WhatsApp
  const [evoUrl, setEvoUrl] = useState("");
  const [evoKey, setEvoKey] = useState("");
  const [evoInstance, setEvoInstance] = useState("");

  // Sending rules
  const [dailyLimit, setDailyLimit] = useState(30);
  const [startTime, setStartTime] = useState("07:00");
  const [endTime, setEndTime] = useState("18:30");
  const [minInterval, setMinInterval] = useState(180);
  const [maxInterval, setMaxInterval] = useState(360);

  async function loadSettings() {
    setLoading(true);
    try {
      const data = await api.getSettings();
      if (data?.google_maps) {
        setGoogleConfigured(data.google_maps.is_configured);
      }
      if (data?.whatsapp) {
        setEvoUrl(data.whatsapp.evolution_url || "");
        setEvoInstance(data.whatsapp.evolution_instance || "");
      }
      if (data?.sending) {
        setDailyLimit(data.sending.daily_contact_limit || 30);
        setStartTime(data.sending.start_time || "07:00");
        setEndTime(data.sending.end_time || "18:30");
        setMinInterval(data.sending.min_interval_sec || 180);
        setMaxInterval(data.sending.max_interval_sec || 360);
      }
    } catch (err) {
      console.error("Erro ao carregar configurações:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSettings();
  }, []);

  async function handleTestGoogle() {
    setTestingGoogle(true);
    setGoogleTestResult(null);
    try {
      const res = await api.testGooglePlacesConnection(googleKey || undefined);
      setGoogleTestResult(res);
    } catch (err: any) {
      setGoogleTestResult({ success: false, message: err.message });
    } finally {
      setTestingGoogle(false);
    }
  }

  async function handleTestEvolution() {
    setTestingEvo(true);
    setEvoTestResult(null);
    try {
      const res = await api.testEvolutionConnection({
        url: evoUrl,
        api_key: evoKey || undefined,
        instance: evoInstance,
      });
      setEvoTestResult(res);
    } catch (err: any) {
      setEvoTestResult({ success: false, message: err.message });
    } finally {
      setTestingEvo(false);
    }
  }

  async function handleSaveSettings() {
    setSaving(true);
    try {
      const payload: Record<string, any> = {
        EVOLUTION_API_URL: evoUrl,
        EVOLUTION_INSTANCE_NAME: evoInstance,
        DAILY_CONTACT_LIMIT: Math.min(Number(dailyLimit), 30),
        MIN_INTERVAL_BETWEEN_CONTACTS_SEC: Number(minInterval),
        MAX_INTERVAL_BETWEEN_CONTACTS_SEC: Number(maxInterval),
      };

      if (evoKey) {
        payload.EVOLUTION_API_KEY = evoKey;
      }
      if (googleKey) {
        payload.GOOGLE_MAPS_API_KEY = googleKey;
      }

      // Separa horas e minutos do horário permitido
      if (startTime.includes(":")) {
        const [sh, sm] = startTime.split(":");
        payload.SENDING_START_HOUR = Number(sh);
        payload.SENDING_START_MINUTE = Number(sm);
      }
      if (endTime.includes(":")) {
        const [eh, em] = endTime.split(":");
        payload.SENDING_END_HOUR = Number(eh);
        payload.SENDING_END_MINUTE = Number(em);
      }

      await api.updateSettings(payload);
      alert("Configurações gerais salvas com sucesso!");
      setEvoKey("");
      loadSettings();
    } catch (err: any) {
      alert(`Erro: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Header
        title="Configurações do Sistema"
        description="Parâmetros de integração da Evolution API, regras de envio e conformidade"
        actions={
          <button
            onClick={handleSaveSettings}
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition-colors shadow-xs disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Salvar Configurações
          </button>
        }
      />

      <main className="p-8 space-y-8 flex-1 overflow-y-auto max-w-4xl text-xs">
        {/* Bloco 0: Google Maps & Places API */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-600" />
              <h2 className="text-sm font-semibold text-slate-900">Google Maps — Google Places API</h2>
            </div>
            <span
              className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                googleConfigured ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"
              }`}
            >
              {googleConfigured ? "Ativo no Google Places" : "Usando OpenStreetMap (Fallback)"}
            </span>
          </div>

          <p className="text-slate-600">
            Insira sua chave oficial da Google Places API (Google Maps Platform). Com a chave configurada, as buscas no Extrator de Leads consultarão o Google Maps oficial trazendo telefones completos, avaliações reais, websites e endereços exatos.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block font-medium text-slate-700 mb-1">
                Google Places API Key (Google Cloud Console)
              </label>
              <input
                type="password"
                placeholder={googleConfigured ? "••••••••••••••••••••••••" : "AIzaSy..."}
                value={googleKey}
                onChange={(e) => setGoogleKey(e.target.value)}
                className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900 font-mono text-xs"
              />
              <span className="text-[10px] text-slate-600 block mt-0.5">
                Chave armazenada no backend. Se não configurada, o sistema utiliza o OpenStreetMap público como fallback gratuito.
              </span>
            </div>
          </div>

          {googleTestResult && (
            <div
              className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                googleTestResult.success
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  : "bg-red-50 text-red-800 border border-red-200"
              }`}
            >
              {googleTestResult.success ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              )}
              <span>{typeof googleTestResult.message === "string" ? googleTestResult.message : JSON.stringify(googleTestResult.message)}</span>
            </div>
          )}

          <div className="pt-2 flex justify-end">
            <button
              type="button"
              onClick={handleTestGoogle}
              disabled={testingGoogle || (!googleKey && !googleConfigured)}
              className="py-2 px-3.5 border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium rounded-lg text-xs flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              {testingGoogle ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 text-amber-500" />}
              Testar Conexão Google Places
            </button>
          </div>
        </div>

        {/* Bloco 1: WhatsApp Evolution API */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-emerald-600" />
              <h2 className="text-sm font-semibold text-slate-900">WhatsApp — Evolution API</h2>
            </div>
            <span className="text-[11px] text-slate-600 font-medium">Instância Própria</span>
          </div>

          <p className="text-slate-600">
            Conecte sua instância oficial da Evolution API para envio de mensagens, acompanhamento de entrega e captura de respostas via webhook idempotente.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block font-medium text-slate-700 mb-1">URL do Servidor Evolution API *</label>
              <input
                type="text"
                placeholder="https://sua-evolution-api.com"
                value={evoUrl}
                onChange={(e) => setEvoUrl(e.target.value)}
                className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900 font-mono text-xs"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">Nome da Instância *</label>
              <input
                type="text"
                placeholder="ex: prospect_carlos"
                value={evoInstance}
                onChange={(e) => setEvoInstance(e.target.value)}
                className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900 text-xs"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">API Key da Evolution</label>
              <input
                type="password"
                placeholder="Cole uma nova chave para atualizar..."
                value={evoKey}
                onChange={(e) => setEvoKey(e.target.value)}
                className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900 font-mono text-xs"
              />
              <span className="text-[10px] text-slate-600 block mt-0.5">
                Armazenada com segurança no backend.
              </span>
            </div>
          </div>

          {evoTestResult && (
            <div
              className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                evoTestResult.success
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  : "bg-red-50 text-red-800 border border-red-200"
              }`}
            >
              {evoTestResult.success ? <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" /> : <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />}
              <span>{typeof evoTestResult.message === "string" ? evoTestResult.message : JSON.stringify(evoTestResult.message)}</span>
            </div>
          )}

          <div className="pt-2 flex justify-end">
            <button
              type="button"
              onClick={handleTestEvolution}
              disabled={testingEvo || !evoUrl || !evoInstance}
              className="py-2 px-3.5 border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium rounded-lg text-xs flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              {testingEvo ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 text-amber-500" />}
              Testar Conexão Evolution
            </button>
          </div>
        </div>

        {/* Bloco 2: Regras de Envio e Limite Obrigatório */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-600" />
              <h2 className="text-sm font-semibold text-slate-900">Políticas de Envio e Compliance</h2>
            </div>
            <span className="text-[10px] uppercase font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
              Regras Rígidas de Proteção
            </span>
          </div>

          <p className="text-slate-600">
            Estas regras protegem o seu número contra bloqueios no WhatsApp e garantem que o limite diário e a janela permitida sejam respeitados transacionalmente pelo backend.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block font-medium text-slate-700 mb-1">
                Limite Diário Global de Contatos Únicos *
              </label>
              <input
                type="number"
                max={30}
                min={1}
                value={dailyLimit}
                onChange={(e) => setDailyLimit(Math.min(30, Number(e.target.value)))}
                className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900 font-bold"
              />
              <span className="text-[10px] text-slate-600 block mt-0.5">
                Travado no máximo em 30 contatos únicos por dia across todas as campanhas.
              </span>
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">Fuso Horário Operacional</label>
              <input
                type="text"
                disabled
                value="America/Sao_Paulo (Horário de Brasília)"
                className="w-full p-2.5 border border-slate-200 rounded-lg bg-slate-50 text-slate-600"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">Início da Janela de Envio</label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
              />
              <span className="text-[10px] text-slate-600 block mt-0.5">Padrão: 07:00</span>
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">Término da Janela de Envio</label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
              />
              <span className="text-[10px] text-slate-600 block mt-0.5">Padrão: 18:30 (Pausa automática)</span>
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">
                Intervalo Mínimo Entre Contatos (segundos)
              </label>
              <input
                type="number"
                min={60}
                value={minInterval}
                onChange={(e) => setMinInterval(Number(e.target.value))}
                className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
              />
              <span className="text-[10px] text-slate-600 block mt-0.5">Padrão: 180s (3 minutos)</span>
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">
                Intervalo Máximo Entre Contatos (segundos)
              </label>
              <input
                type="number"
                min={120}
                value={maxInterval}
                onChange={(e) => setMaxInterval(Number(e.target.value))}
                className="w-full p-2.5 border border-slate-200 rounded-lg text-slate-900"
              />
              <span className="text-[10px] text-slate-600 block mt-0.5">Padrão: 360s (6 minutos com jitter humano)</span>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
