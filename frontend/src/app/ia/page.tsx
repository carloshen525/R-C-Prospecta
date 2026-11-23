"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import {
  Bot,
  Key,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Save,
  Zap,
  ArrowRightLeft,
  Sparkles,
  ExternalLink
} from "lucide-react";
import { api } from "@/lib/api";

export default function IACentralPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({});

  // Keys & models
  const [openaiKey, setOpenaiKey] = useState("");
  const [openaiModel, setOpenaiModel] = useState("gpt-4o-mini");
  const [groqKey, setGroqKey] = useState("");
  const [groqModel, setGroqModel] = useState("llama-3.3-70b-versatile");
  const [geminiKey, setGeminiKey] = useState("");
  const [geminiModel, setGeminiModel] = useState("gemini-1.5-flash");

  const [defaultProvider, setDefaultProvider] = useState("gemini");
  const [fallbackProvider, setFallbackProvider] = useState("groq");
  const [savedSettings, setSavedSettings] = useState<any>(null);

  async function loadSettings() {
    setLoading(true);
    try {
      const data = await api.getSettings();
      if (data?.ai) {
        setSavedSettings(data.ai);
        setDefaultProvider(data.ai.default_provider || "gemini");
        setFallbackProvider(data.ai.fallback_provider || "groq");
        setOpenaiModel(data.ai.openai_model || "gpt-4o-mini");
        setGroqModel(data.ai.groq_model || "llama-3.3-70b-versatile");
        setGeminiModel(data.ai.gemini_model || "gemini-1.5-flash");
      }
    } catch (err) {
      console.error("Erro ao carregar configurações de IA:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSettings();
  }, []);

  async function handleTest(provider: string) {
    setTesting(provider);
    try {
      let keyToTest = undefined;
      if (provider === "openai" && openaiKey) keyToTest = openaiKey;
      if (provider === "groq" && groqKey) keyToTest = groqKey;
      if (provider === "gemini" && geminiKey) keyToTest = geminiKey;

      const res = await api.testAiConnection(provider, keyToTest);
      setTestResults({
        ...testResults,
        [provider]: { success: res.success, message: res.message },
      });
    } catch (err: any) {
      setTestResults({
        ...testResults,
        [provider]: { success: false, message: err.message },
      });
    } finally {
      setTesting(null);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      const payload: Record<string, any> = {
        DEFAULT_AI_PROVIDER: defaultProvider,
        FALLBACK_AI_PROVIDER: fallbackProvider,
        OPENAI_MODEL: openaiModel,
        GROQ_MODEL: groqModel,
        GEMINI_MODEL: geminiModel,
      };

      if (openaiKey) payload.OPENAI_API_KEY = openaiKey;
      if (groqKey) payload.GROQ_API_KEY = groqKey;
      if (geminiKey) payload.GEMINI_API_KEY = geminiKey;

      await api.updateSettings(payload);
      alert("Configurações de Inteligência Artificial atualizadas com sucesso!");
      setOpenaiKey("");
      setGroqKey("");
      setGeminiKey("");
      loadSettings();
    } catch (err: any) {
      alert(`Erro ao salvar: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Header
        title="Central de Inteligência Artificial"
        description="Gestão de provedores, chaves de API e redundância de fallback para geração de mensagens"
        actions={
          <button
            onClick={handleSave}
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition-colors shadow-xs disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Salvar Alterações
          </button>
        }
      />

      <main className="p-8 space-y-8 flex-1 overflow-y-auto">
        {/* Painel de Roteamento & Fallback */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
            <ArrowRightLeft className="w-4 h-4 text-emerald-600" />
            <h2 className="text-sm font-semibold text-slate-900">Roteamento e Fallback Automático</h2>
          </div>
          <p className="text-xs text-slate-600 mb-6">
            Caso o provedor principal sofra instabilidade temporária ou esgote a quota de requisições, o backend do Prospect AI acionará imediatamente o provedor alternativo com validação de esquema JSON.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl space-y-2">
              <label className="block font-semibold text-slate-900">
                1. Provedor Padrão Principal
              </label>
              <select
                value={defaultProvider}
                onChange={(e) => setDefaultProvider(e.target.value)}
                className="w-full p-2.5 bg-white border border-slate-200 rounded-lg text-slate-900"
              >
                <option value="gemini">Google Gemini</option>
                <option value="groq">Groq</option>
                <option value="openai">OpenAI</option>
              </select>
              <span className="text-[11px] text-slate-600 block">
                Primeira escolha executada em todas as gerações de mensagens.
              </span>
            </div>

            <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl space-y-2">
              <label className="block font-semibold text-slate-900">
                2. Provedor Alternativo (Fallback)
              </label>
              <select
                value={fallbackProvider}
                onChange={(e) => setFallbackProvider(e.target.value)}
                className="w-full p-2.5 bg-white border border-slate-200 rounded-lg text-slate-900"
              >
                <option value="groq">Groq</option>
                <option value="gemini">Google Gemini</option>
                <option value="openai">OpenAI</option>
              </select>
              <span className="text-[11px] text-slate-600 block">
                Acionado em caso de erro 429 ou indisponibilidade da API primária.
              </span>
            </div>
          </div>
        </div>

        {/* Cards dos 3 Provedores */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Google Gemini */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="font-semibold text-slate-900 text-sm">Google Gemini</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                    savedSettings?.gemini_configured
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-slate-100 text-slate-700"
                  }`}
                >
                  {savedSettings?.gemini_configured ? "Configurado" : "Pendente"}
                </span>
              </div>

              <div className="space-y-3 mt-4 text-xs">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block font-medium text-slate-700">API Key</label>
                    <a
                      href="https://aistudio.google.com/app/apikey"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-emerald-600 hover:text-emerald-700 hover:underline inline-flex items-center gap-1 font-medium"
                    >
                      <span>Gerar chave no Google AI Studio</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <input
                    type="password"
                    placeholder={savedSettings?.gemini_key_masked || "Cole sua Gemini API Key..."}
                    value={geminiKey}
                    onChange={(e) => setGeminiKey(e.target.value)}
                    className="w-full p-2 border border-slate-200 rounded-lg text-slate-900 font-mono text-[11px]"
                  />
                </div>

                <div>
                  <label className="block font-medium text-slate-700 mb-1">Modelo</label>
                  <select
                    value={geminiModel}
                    onChange={(e) => setGeminiModel(e.target.value)}
                    className="w-full p-2 border border-slate-200 rounded-lg bg-white text-slate-900"
                  >
                    <option value="gemini-1.5-flash">gemini-1.5-flash (Rápido / Recomendado)</option>
                    <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                    <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                  </select>
                </div>
              </div>
            </div>

            <div>
              {testResults["gemini"] && (
                <div
                  className={`p-2 rounded text-[11px] mb-3 ${
                    testResults["gemini"].success
                      ? "bg-emerald-50 text-emerald-800"
                      : "bg-red-50 text-red-800"
                  }`}
                >
                  {testResults["gemini"].message}
                </div>
              )}

              <button
                type="button"
                onClick={() => handleTest("gemini")}
                disabled={testing === "gemini"}
                className="w-full py-2 px-3 border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium rounded-lg text-xs transition-colors flex items-center justify-center gap-1.5"
              >
                {testing === "gemini" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 text-amber-500" />}
                Testar Conexão
              </button>
            </div>
          </div>

          {/* Groq */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="font-semibold text-slate-900 text-sm">Groq</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                    savedSettings?.groq_configured
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-slate-100 text-slate-700"
                  }`}
                >
                  {savedSettings?.groq_configured ? "Configurado" : "Pendente"}
                </span>
              </div>

              <div className="space-y-3 mt-4 text-xs">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block font-medium text-slate-700">API Key</label>
                    <a
                      href="https://console.groq.com/keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-emerald-600 hover:text-emerald-700 hover:underline inline-flex items-center gap-1 font-medium"
                    >
                      <span>Gerar chave no Groq Console</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <input
                    type="password"
                    placeholder={savedSettings?.groq_key_masked || "gsk_..."}
                    value={groqKey}
                    onChange={(e) => setGroqKey(e.target.value)}
                    className="w-full p-2 border border-slate-200 rounded-lg text-slate-900 font-mono text-[11px]"
                  />
                </div>

                <div>
                  <label className="block font-medium text-slate-700 mb-1">Modelo</label>
                  <select
                    value={groqModel}
                    onChange={(e) => setGroqModel(e.target.value)}
                    className="w-full p-2 border border-slate-200 rounded-lg bg-white text-slate-900"
                  >
                    <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                    <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                    <option value="mixtral-8x7b-32768">mixtral-8x7b-32768</option>
                  </select>
                </div>
              </div>
            </div>

            <div>
              {testResults["groq"] && (
                <div
                  className={`p-2 rounded text-[11px] mb-3 ${
                    testResults["groq"].success
                      ? "bg-emerald-50 text-emerald-800"
                      : "bg-red-50 text-red-800"
                  }`}
                >
                  {testResults["groq"].message}
                </div>
              )}

              <button
                type="button"
                onClick={() => handleTest("groq")}
                disabled={testing === "groq"}
                className="w-full py-2 px-3 border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium rounded-lg text-xs transition-colors flex items-center justify-center gap-1.5"
              >
                {testing === "groq" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 text-amber-500" />}
                Testar Conexão
              </button>
            </div>
          </div>

          {/* OpenAI */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="font-semibold text-slate-900 text-sm">OpenAI</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                    savedSettings?.openai_configured
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-slate-100 text-slate-700"
                  }`}
                >
                  {savedSettings?.openai_configured ? "Configurado" : "Pendente"}
                </span>
              </div>

              <div className="space-y-3 mt-4 text-xs">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block font-medium text-slate-700">API Key</label>
                    <a
                      href="https://platform.openai.com/api-keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-emerald-600 hover:text-emerald-700 hover:underline inline-flex items-center gap-1 font-medium"
                    >
                      <span>Gerar chave na OpenAI</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <input
                    type="password"
                    placeholder={savedSettings?.openai_key_masked || "sk-..."}
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    className="w-full p-2 border border-slate-200 rounded-lg text-slate-900 font-mono text-[11px]"
                  />
                </div>

                <div>
                  <label className="block font-medium text-slate-700 mb-1">Modelo</label>
                  <select
                    value={openaiModel}
                    onChange={(e) => setOpenaiModel(e.target.value)}
                    className="w-full p-2 border border-slate-200 rounded-lg bg-white text-slate-900"
                  >
                    <option value="gpt-4o-mini">gpt-4o-mini (Econômico)</option>
                    <option value="gpt-4o">gpt-4o (Avançado)</option>
                  </select>
                </div>
              </div>
            </div>

            <div>
              {testResults["openai"] && (
                <div
                  className={`p-2 rounded text-[11px] mb-3 ${
                    testResults["openai"].success
                      ? "bg-emerald-50 text-emerald-800"
                      : "bg-red-50 text-red-800"
                  }`}
                >
                  {testResults["openai"].message}
                </div>
              )}

              <button
                type="button"
                onClick={() => handleTest("openai")}
                disabled={testing === "openai"}
                className="w-full py-2 px-3 border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium rounded-lg text-xs transition-colors flex items-center justify-center gap-1.5"
              >
                {testing === "openai" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 text-amber-500" />}
                Testar Conexão
              </button>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
