"use client";

import { useEffect, useState, useRef } from "react";
import { Header } from "@/components/layout/Header";
import {
  MessageSquare,
  Search,
  Send,
  Phone,
  Globe,
  Star,
  CheckCheck,
  Check,
  Sparkles,
  ShieldAlert,
  ThumbsUp,
  ThumbsDown,
  UserX,
  ExternalLink,
  Loader2
} from "lucide-react";
import { api } from "@/lib/api";

export default function WhatsAppCRMPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [currentConvData, setCurrentConvData] = useState<any>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingThread, setLoadingThread] = useState(false);
  const [search, setSearch] = useState("");
  const [replyText, setReplyText] = useState("");
  const [sendingReply, setSendingReply] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  async function loadConversations() {
    setLoadingList(true);
    try {
      const data = await api.listConversations();
      setConversations(data || []);
      if (data && data.length > 0 && selectedId === null) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      console.error("Erro ao carregar conversas:", err);
    } finally {
      setLoadingList(false);
    }
  }

  async function loadConversationDetail(id: number) {
    setLoadingThread(true);
    try {
      const data = await api.getConversationDetail(id);
      setCurrentConvData(data);
    } catch (err) {
      console.error("Erro ao carregar conversa:", err);
    } finally {
      setLoadingThread(false);
    }
  }

  useEffect(() => {
    loadConversations();
    const interval = setInterval(loadConversations, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedId) {
      loadConversationDetail(selectedId);
    }
  }, [selectedId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentConvData?.events]);

  async function handleSendReply(e: React.FormEvent) {
    e.preventDefault();
    if (!replyText.trim() || !selectedId || sendingReply) return;

    setSendingReply(true);
    try {
      await api.sendConversationReply(selectedId, replyText);
      setReplyText("");
      await loadConversationDetail(selectedId);
      loadConversations();
    } catch (err: any) {
      alert(`Falha no envio da resposta: ${err.message}`);
    } finally {
      setSendingReply(false);
    }
  }

  async function handleUpdateStatus(status: string) {
    if (!selectedId) return;
    try {
      await api.updateConversationStatus(selectedId, status);
      await loadConversationDetail(selectedId);
      loadConversations();
    } catch (err: any) {
      alert(`Erro ao atualizar status: ${err.message}`);
    }
  }

  async function handleOptOut() {
    if (!selectedId) return;
    if (!confirm("Confirmar solicitação de opt-out? O lead será adicionado à lista de bloqueio e não receberá novas mensagens.")) return;
    try {
      await api.optOutConversation(selectedId);
      await loadConversationDetail(selectedId);
      loadConversations();
    } catch (err: any) {
      alert(`Erro: ${err.message}`);
    }
  }

  const filteredConversations = conversations.filter(
    (c) =>
      c.company_name?.toLowerCase().includes(search.toLowerCase()) ||
      c.phone.includes(search)
  );

  return (
    <>
      <Header
        title="WhatsApp & Conversas"
        description="Atendimento direto, histórico de interações e acompanhamento de respostas"
      />

      <main className="flex-1 flex overflow-hidden">
        {/* Coluna 1: Lista de Contatos */}
        <section className="w-80 bg-white border-r border-slate-200 flex flex-col h-[calc(100vh-64px)]">
          <div className="p-3 border-b border-slate-100">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-600 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Buscar conversa..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 text-slate-900"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {loadingList && conversations.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-600">Carregando conversas...</div>
            ) : filteredConversations.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-600">
                Nenhuma conversa encontrada.
              </div>
            ) : (
              filteredConversations.map((c) => {
                const isSelected = c.id === selectedId;
                return (
                  <button
                    key={c.id}
                    onClick={() => setSelectedId(c.id)}
                    className={`w-full text-left p-3.5 flex items-start gap-3 transition-colors ${
                      isSelected ? "bg-emerald-50/70 border-r-2 border-emerald-600" : "hover:bg-slate-50"
                    }`}
                  >
                    <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center font-semibold text-slate-700 text-xs shrink-0">
                      {c.company_name ? c.company_name[0].toUpperCase() : "E"}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-xs text-slate-900 truncate">
                          {c.company_name || c.phone}
                        </span>
                        {c.unread_count > 0 && (
                          <span className="w-4 h-4 rounded-full bg-emerald-600 text-white text-[10px] flex items-center justify-center font-bold">
                            {c.unread_count}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-600 font-mono mt-0.5">{c.phone}</p>
                      <div className="flex items-center gap-1.5 mt-1">
                        <span
                          className={`text-[9px] font-semibold px-1.5 py-0.2 rounded ${
                            c.status === "interessado"
                              ? "bg-purple-100 text-purple-800"
                              : c.status === "finalizada"
                              ? "bg-slate-100 text-slate-600"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {c.status}
                        </span>
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </section>

        {/* Coluna 2: Chat / Timeline Selecionada */}
        <section className="flex-1 bg-slate-50 flex flex-col h-[calc(100vh-64px)]">
          {currentConvData ? (
            <>
              {/* Header do Chat */}
              <div className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900 text-sm">
                    {currentConvData.lead?.company_name || currentConvData.conversation?.phone}
                  </h3>
                  <span className="text-xs text-slate-600 font-mono">
                    {currentConvData.conversation?.phone}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-600 font-medium">Status da Negociação:</span>
                  <span className="px-2 py-0.5 rounded-full font-semibold text-[10px] bg-emerald-100 text-emerald-800 uppercase">
                    {currentConvData.conversation?.status}
                  </span>
                </div>
              </div>

              {/* Lista de Mensagens */}
              <div className="flex-1 p-6 overflow-y-auto space-y-3">
                {loadingThread ? (
                  <div className="py-20 text-center text-xs text-slate-600">Carregando mensagens...</div>
                ) : !currentConvData.events || currentConvData.events.length === 0 ? (
                  <div className="text-center py-20 text-xs text-slate-600">
                    Nenhuma mensagem registrada nesta conversa ainda.
                  </div>
                ) : (
                  currentConvData.events.map((evt: any) => {
                    const isOutgoing = evt.direction === "outgoing";
                    return (
                      <div
                        key={evt.id}
                        className={`flex flex-col ${isOutgoing ? "items-end" : "items-start"}`}
                      >
                        <div
                          className={`max-w-[70%] p-3.5 rounded-2xl text-xs shadow-2xs leading-relaxed whitespace-pre-wrap ${
                            isOutgoing
                              ? "bg-emerald-600 text-white rounded-br-xs"
                              : "bg-white text-slate-800 border border-slate-200/90 rounded-bl-xs"
                          }`}
                        >
                          <p>{evt.message_content}</p>
                          <div
                            className={`flex items-center justify-end gap-1 mt-1.5 text-[10px] ${
                              isOutgoing ? "text-emerald-100" : "text-slate-600"
                            }`}
                          >
                            <span>
                              {new Date(evt.created_at).toLocaleTimeString("pt-BR", {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                            {isOutgoing && <CheckCheck className="w-3 h-3 text-emerald-200" />}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Barra de Resposta Manual */}
              <form
                onSubmit={handleSendReply}
                className="p-3.5 bg-white border-t border-slate-200 flex items-center gap-2"
              >
                <input
                  type="text"
                  placeholder="Digite sua resposta manual via WhatsApp..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  className="flex-1 px-4 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 text-slate-900"
                />
                <button
                  type="submit"
                  disabled={sendingReply || !replyText.trim()}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg text-xs flex items-center gap-1.5 transition-colors disabled:opacity-50 shadow-xs"
                >
                  {sendingReply ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                  <span>Enviar</span>
                </button>
              </form>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-xs text-slate-600">
              Selecione uma conversa ao lado para visualizar a timeline
            </div>
          )}
        </section>

        {/* Coluna 3: Informações do Lead & Ações de CRM */}
        {currentConvData?.lead && (
          <aside className="w-80 bg-white border-l border-slate-200 p-5 flex flex-col justify-between h-[calc(100vh-64px)] overflow-y-auto text-xs space-y-6">
            <div className="space-y-4">
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-600 tracking-wider">
                  Detalhes do Lead
                </span>
                <h4 className="font-semibold text-slate-900 text-sm mt-1">
                  {currentConvData.lead.company_name}
                </h4>
                <p className="text-slate-600">
                  {currentConvData.lead.segment} • {currentConvData.lead.city} - {currentConvData.lead.state}
                </p>
              </div>

              <div className="space-y-2 pt-3 border-t border-slate-100 text-slate-700">
                <div className="flex items-center gap-2">
                  <Phone className="w-3.5 h-3.5 text-slate-600" />
                  <span className="font-mono">{currentConvData.lead.phone}</span>
                </div>

                {currentConvData.lead.website && (
                  <div className="flex items-center gap-2">
                    <Globe className="w-3.5 h-3.5 text-slate-600" />
                    <a
                      href={
                        currentConvData.lead.website.startsWith("http")
                          ? currentConvData.lead.website
                          : `https://${currentConvData.lead.website}`
                      }
                      target="_blank"
                      rel="noreferrer"
                      className="text-emerald-600 hover:underline truncate"
                    >
                      {currentConvData.lead.website}
                    </a>
                  </div>
                )}
              </div>

              {/* Análise de Site */}
              {currentConvData.lead.website_data && (
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                  <span className="font-semibold text-emerald-800 flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-emerald-600" /> Análise do Site
                  </span>
                  <p className="text-slate-600 text-[11px]">
                    {currentConvData.lead.website_data.about_summary || "Dados públicos obtidos"}
                  </p>
                </div>
              )}
            </div>

            {/* Ações de Classificação de CRM */}
            <div className="space-y-2 pt-4 border-t border-slate-100">
              <span className="text-[10px] uppercase font-bold text-slate-600 tracking-wider block">
                Classificar Oportunidade
              </span>

              <button
                onClick={() => handleUpdateStatus("interessado")}
                className="w-full py-2 px-3 bg-purple-50 hover:bg-purple-100 text-purple-700 font-medium rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors"
              >
                <ThumbsUp className="w-3.5 h-3.5" /> Marcar como Interessado
              </button>

              <button
                onClick={() => handleUpdateStatus("sem_interesse")}
                className="w-full py-2 px-3 bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors"
              >
                <ThumbsDown className="w-3.5 h-3.5" /> Marcar como Sem Interesse
              </button>

              <button
                onClick={handleOptOut}
                className="w-full py-2 px-3 bg-red-50 hover:bg-red-100 text-red-700 font-medium rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors"
              >
                <UserX className="w-3.5 h-3.5" /> Solicitação de Opt-out (Bloquear)
              </button>
            </div>
          </aside>
        )}
      </main>
    </>
  );
}
