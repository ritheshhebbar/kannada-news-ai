"use client";

import { useState } from "react";
import { Sparkles, Send, Bot, User, Loader2, CheckCircle2, HelpCircle } from "lucide-react";
import { api, getSessionId } from "@/lib/api";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  citedSentences?: number[];
  grounded?: boolean;
}

interface AskArticleChatProps {
  articleId: number;
  onSelectEvidence?: (sentenceIdx: number) => void;
}

export function AskArticleChat({ articleId, onSelectEvidence }: AskArticleChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "assistant",
      text: "Ask me anything about this article. My answers are strictly grounded in the translated sentences with citations.",
      citedSentences: [],
      grounded: true,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sampleQuestions = [
    "Who is the main person or entity involved?",
    "What numbers or statistics are mentioned?",
    "Where and when did this event take place?",
  ];

  const handleSend = async (questionText: string) => {
    const q = questionText.trim();
    if (!q || loading) return;

    const userMsg: Message = {
      id: "user_" + Date.now(),
      sender: "user",
      text: q,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const sid = getSessionId();
      const res = await api.askArticle(articleId, q, sid);

      const botMsg: Message = {
        id: "bot_" + Date.now(),
        sender: "assistant",
        text: res.answer,
        citedSentences: res.cited_sentences || [],
        grounded: res.grounded,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errMsg: Message = {
        id: "err_" + Date.now(),
        sender: "assistant",
        text: err.message || "Failed to generate answer. Please try again.",
        grounded: false,
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col h-[480px]">
      {/* Header */}
      <div className="flex items-center justify-between pb-3.5 border-b border-slate-100 mb-3 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-violet-600 text-white flex items-center justify-center shadow-xs">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
              Ask the Article
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold">
                Grounded AI
              </span>
            </h3>
            <p className="text-[11px] text-slate-500">Strictly answers from translated sentences</p>
          </div>
        </div>

        {messages.length > 2 && (
          <button
            type="button"
            onClick={() =>
              setMessages([
                {
                  id: "welcome",
                  sender: "assistant",
                  text: "Ask me anything about this article.",
                  citedSentences: [],
                  grounded: true,
                },
              ])
            }
            className="text-[11px] text-slate-400 hover:text-slate-600 transition"
          >
            Clear
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start gap-2 ${
              m.sender === "user" ? "flex-row-reverse" : "flex-row"
            }`}
          >
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] ${
                m.sender === "user"
                  ? "bg-slate-800 text-white"
                  : "bg-indigo-100 text-indigo-700 font-bold"
              }`}
            >
              {m.sender === "user" ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
            </div>

            <div
              className={`max-w-[85%] rounded-xl p-3 ${
                m.sender === "user"
                  ? "bg-indigo-600 text-white rounded-tr-none font-medium"
                  : "bg-slate-50 border border-slate-200/80 text-slate-800 rounded-tl-none shadow-2xs"
              }`}
            >
              <p className="leading-relaxed whitespace-pre-wrap">{m.text}</p>

              {/* Citations Pill Bar */}
              {m.citedSentences && m.citedSentences.length > 0 && (
                <div className="mt-2 pt-1.5 border-t border-slate-200/60 flex flex-wrap items-center gap-1.5">
                  <span className="text-[10px] font-semibold text-slate-500 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Evidence:
                  </span>
                  {m.citedSentences.map((idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => onSelectEvidence?.(idx)}
                      title={`Jump to sentence S${idx}`}
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-100 hover:bg-indigo-200 text-indigo-800 font-bold transition cursor-pointer"
                    >
                      S{idx}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-slate-400 p-2 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
            <span className="text-[11px]">Searching article facts & generating answer...</span>
          </div>
        )}
      </div>

      {/* Suggested Starter Questions (when few messages) */}
      {messages.length <= 2 && !loading && (
        <div className="pt-2 pb-1.5 flex flex-wrap gap-1.5 flex-shrink-0">
          {sampleQuestions.map((sq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSend(sq)}
              className="text-[11px] bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 text-slate-600 hover:text-indigo-700 px-2.5 py-1 rounded-full transition text-left cursor-pointer"
            >
              {sq}
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend(input);
        }}
        className="mt-3 pt-2.5 border-t border-slate-100 flex items-center gap-2 flex-shrink-0"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about this story..."
          disabled={loading}
          className="flex-1 text-xs p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="p-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-xs transition disabled:opacity-50 cursor-pointer flex-shrink-0"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}

