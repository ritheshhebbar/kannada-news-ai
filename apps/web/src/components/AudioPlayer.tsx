"use client";

import { useState, useEffect, useRef } from "react";
import { Volume2, Play, Pause, Square } from "lucide-react";

interface AudioPlayerProps {
  englishSummary?: string;
  englishHeadline?: string;
  englishKeyPoints?: Array<{ text: string }>;
  kannadaBody?: string;
}

export function AudioPlayer({
  englishSummary,
  englishHeadline,
  englishKeyPoints = [],
  kannadaBody,
}: AudioPlayerProps) {
  const [mounted, setMounted] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [audioMode, setAudioMode] = useState<"summary" | "kannada">("summary");
  const [rate, setRate] = useState<number>(1.0);
  const [supported, setSupported] = useState(false);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);

  const synthRef = useRef<SpeechSynthesis | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    setMounted(true);
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      setSupported(true);
      synthRef.current = window.speechSynthesis;

      const updateVoices = () => {
        if (synthRef.current) {
          try {
            setAvailableVoices(synthRef.current.getVoices());
          } catch (e) {
            // ignore
          }
        }
      };

      updateVoices();
      if (window.speechSynthesis && window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = updateVoices;
      }
    }

    return () => {
      if (synthRef.current) {
        try {
          synthRef.current.cancel();
        } catch (e) {
          // ignore
        }
      }
    };
  }, []);

  const getAudioText = () => {
    if (audioMode === "kannada") {
      return kannadaBody || "ಯಾವುದೇ ಪಠ್ಯ ಲಭ್ಯವಿಲ್ಲ.";
    }

    let text = "";
    if (englishHeadline) {
      text += `Headline: ${englishHeadline}. `;
    }
    if (englishSummary) {
      text += `Summary: ${englishSummary}. `;
    }
    if (englishKeyPoints.length > 0) {
      text += "Key points: ";
      englishKeyPoints.forEach((kp, idx) => {
        text += `Point ${idx + 1}: ${kp.text}. `;
      });
    }
    return text || "No summary available to read aloud.";
  };

  const handlePlay = () => {
    if (!synthRef.current) return;

    if (isPaused) {
      synthRef.current.resume();
      setIsPaused(false);
      setIsPlaying(true);
      return;
    }

    synthRef.current.cancel();

    const textToSpeak = getAudioText();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utteranceRef.current = utterance;
    utterance.rate = rate;

    if (audioMode === "kannada") {
      const knVoice = availableVoices.find(
        (v) => v.lang.startsWith("kn") || v.lang.includes("kn-IN")
      );
      if (knVoice) utterance.voice = knVoice;
      else utterance.lang = "kn-IN";
    } else {
      const enVoice = availableVoices.find(
        (v) =>
          v.lang.startsWith("en-IN") ||
          v.lang.startsWith("en-GB") ||
          v.lang.startsWith("en-US")
      );
      if (enVoice) utterance.voice = enVoice;
      else utterance.lang = "en-US";
    }

    utterance.onend = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };

    utterance.onerror = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };

    synthRef.current.speak(utterance);
    setIsPlaying(true);
    setIsPaused(false);
  };

  const handlePause = () => {
    if (!synthRef.current) return;
    synthRef.current.pause();
    setIsPaused(true);
    setIsPlaying(false);
  };

  const handleStop = () => {
    if (!synthRef.current) return;
    synthRef.current.cancel();
    setIsPlaying(false);
    setIsPaused(false);
  };

  const cycleSpeed = () => {
    const speeds = [1.0, 1.25, 1.5];
    const nextIdx = (speeds.indexOf(rate) + 1) % speeds.length;
    const nextRate = speeds[nextIdx];
    setRate(nextRate);
    if (isPlaying) {
      handleStop();
      setTimeout(handlePlay, 100);
    }
  };

  if (!mounted || !supported) return null;

  return (
    <div className="bg-gradient-to-r from-indigo-50/70 via-white to-indigo-50/40 border border-indigo-100 rounded-xl p-3.5 mb-6 flex flex-wrap items-center justify-between gap-3 shadow-xs">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-xs">
          {isPlaying ? (
            <Volume2 className="w-5 h-5 animate-pulse text-indigo-100" />
          ) : (
            <Volume2 className="w-5 h-5" />
          )}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-xs font-bold text-slate-800 tracking-wide uppercase">
              Audio News Briefing
            </h4>
            {isPlaying && (
              <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                Playing
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-500">
            Listen to verified English summary or original Kannada audio
          </p>
        </div>
      </div>

      <div className="flex items-center flex-wrap gap-2">
        {/* Language selector */}
        <div className="flex items-center bg-slate-100/90 p-0.5 rounded-lg text-xs font-medium">
          <button
            type="button"
            onClick={() => {
              if (audioMode !== "summary") {
                handleStop();
                setAudioMode("summary");
              }
            }}
            className={`px-2.5 py-1 rounded-md transition text-xs ${
              audioMode === "summary"
                ? "bg-white text-indigo-700 shadow-xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            English Brief
          </button>
          <button
            type="button"
            onClick={() => {
              if (audioMode !== "kannada") {
                handleStop();
                setAudioMode("kannada");
              }
            }}
            className={`px-2.5 py-1 rounded-md transition text-xs ${
              audioMode === "kannada"
                ? "bg-white text-indigo-700 shadow-xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Kannada
          </button>
        </div>

        {/* Speed toggle */}
        <button
          type="button"
          onClick={cycleSpeed}
          title="Change playback speed"
          className="text-xs font-semibold px-2 py-1 bg-white border border-slate-200 hover:border-indigo-300 text-slate-700 rounded-lg shadow-xs transition"
        >
          {rate}x
        </button>

        {/* Playback Controls */}
        <div className="flex items-center gap-1">
          {!isPlaying ? (
            <button
              type="button"
              onClick={handlePlay}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isPaused ? "Resume" : "Listen"}</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={handlePause}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-semibold shadow-xs transition cursor-pointer"
            >
              <Pause className="w-3.5 h-3.5 fill-current" />
              <span>Pause</span>
            </button>
          )}

          {(isPlaying || isPaused) && (
            <button
              type="button"
              onClick={handleStop}
              title="Stop audio"
              className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition cursor-pointer"
            >
              <Square className="w-3.5 h-3.5 fill-current text-slate-600" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
