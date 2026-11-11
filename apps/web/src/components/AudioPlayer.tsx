"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import { Volume2, Play, Pause, Square, FastForward } from "lucide-react";

interface AudioPlayerProps {
  englishSummary?: string;
  englishHeadline?: string;
  englishKeyPoints?: Array<{ text: string }>;
}

export function AudioPlayer({
  englishSummary,
  englishHeadline,
  englishKeyPoints = [],
}: AudioPlayerProps) {
  const [mounted, setMounted] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [rate, setRate] = useState<number>(1.0);
  const [currentChunkIdx, setCurrentChunkIdx] = useState<number>(0);
  const [supported, setSupported] = useState(false);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);

  const synthRef = useRef<SpeechSynthesis | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const isPlayingRef = useRef(false);
  const isPausedRef = useRef(false);
  const rateRef = useRef(1.0);
  const currentChunkIdxRef = useRef(0);

  // Split audio briefing into sentence-level chunks for seamless speed adjustment & resume
  const chunks = useMemo(() => {
    const list: string[] = [];
    if (englishHeadline?.trim()) {
      list.push(`Headline: ${englishHeadline.trim()}.`);
    }
    if (englishSummary?.trim()) {
      const sents = englishSummary
        .split(/(?<=[.?!])\s+/)
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
      list.push(...sents);
    }
    if (englishKeyPoints && englishKeyPoints.length > 0) {
      englishKeyPoints.forEach((kp, idx) => {
        if (kp.text?.trim()) {
          list.push(`Key point ${idx + 1}: ${kp.text.trim()}.`);
        }
      });
    }
    return list;
  }, [englishHeadline, englishSummary, englishKeyPoints]);

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
          isPlayingRef.current = false;
          synthRef.current.cancel();
        } catch (e) {
          // ignore
        }
      }
    };
  }, []);

  const speakChunk = (index: number, speed: number) => {
    if (!synthRef.current || chunks.length === 0) return;

    if (index >= chunks.length) {
      // Completed full briefing
      setIsPlaying(false);
      setIsPaused(false);
      isPlayingRef.current = false;
      isPausedRef.current = false;
      setCurrentChunkIdx(0);
      currentChunkIdxRef.current = 0;
      return;
    }

    currentChunkIdxRef.current = index;
    setCurrentChunkIdx(index);

    const textToSpeak = chunks[index];
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utteranceRef.current = utterance;
    utterance.rate = speed;

    // Pick clear English voice
    const enVoice = availableVoices.find(
      (v) =>
        v.lang.startsWith("en-IN") ||
        v.lang.startsWith("en-GB") ||
        v.lang.startsWith("en-US")
    );
    if (enVoice) {
      utterance.voice = enVoice;
    } else {
      utterance.lang = "en-US";
    }

    utterance.onend = () => {
      if (isPlayingRef.current && !isPausedRef.current) {
        speakChunk(index + 1, rateRef.current);
      }
    };

    utterance.onerror = (e) => {
      // Interrupted errors happen intentionally when speed changes or stop is clicked
      if (e.error !== "interrupted" && e.error !== "canceled") {
        setIsPlaying(false);
        setIsPaused(false);
        isPlayingRef.current = false;
      }
    };

    synthRef.current.speak(utterance);
  };

  const handlePlay = () => {
    if (!synthRef.current || chunks.length === 0) return;

    if (isPaused) {
      synthRef.current.resume();
      setIsPaused(false);
      setIsPlaying(true);
      isPausedRef.current = false;
      isPlayingRef.current = true;
      return;
    }

    synthRef.current.cancel();
    setIsPlaying(true);
    setIsPaused(false);
    isPlayingRef.current = true;
    isPausedRef.current = false;

    speakChunk(currentChunkIdxRef.current, rateRef.current);
  };

  const handlePause = () => {
    if (!synthRef.current) return;
    synthRef.current.pause();
    setIsPaused(true);
    setIsPlaying(false);
    isPausedRef.current = true;
    isPlayingRef.current = false;
  };

  const handleStop = () => {
    if (!synthRef.current) return;
    isPlayingRef.current = false;
    isPausedRef.current = false;
    synthRef.current.cancel();
    setIsPlaying(false);
    setIsPaused(false);
    setCurrentChunkIdx(0);
    currentChunkIdxRef.current = 0;
  };

  // Instant speed adjustment at the current sentence
  const handleSpeedChange = (newRate: number) => {
    setRate(newRate);
    rateRef.current = newRate;

    if (isPlaying) {
      // Cancel current utterance and immediately re-speak from the exact current sentence with the new speed
      if (synthRef.current) {
        synthRef.current.cancel();
        setTimeout(() => {
          if (isPlayingRef.current) {
            speakChunk(currentChunkIdxRef.current, newRate);
          }
        }, 30);
      }
    }
  };

  if (!mounted || !supported || chunks.length === 0) return null;

  const currentSentenceText = chunks[currentChunkIdx] || "";

  return (
    <div className="bg-gradient-to-r from-indigo-50/70 via-white to-indigo-50/40 border border-indigo-100 rounded-xl p-3.5 mb-6 shadow-xs transition">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left: Info & Live State */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-xs flex-shrink-0">
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
                  Playing ({currentChunkIdx + 1}/{chunks.length})
                </span>
              )}
              {isPaused && (
                <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                  Paused
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              Listen to the verified English headline, summary, and key points
            </p>
          </div>
        </div>

        {/* Right: Controls & Speed Selector */}
        <div className="flex items-center flex-wrap gap-2">
          {/* Instant Speed Selector */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-medium border border-slate-200">
            {[1.0, 1.25, 1.5, 2.0].map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => handleSpeedChange(s)}
                title={`Change speed to ${s}x immediately`}
                className={`px-2 py-1 rounded-md text-xs font-semibold transition cursor-pointer ${
                  rate === s
                    ? "bg-white text-indigo-700 shadow-xs font-bold"
                    : "text-slate-500 hover:text-slate-900"
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Play / Pause / Stop Buttons */}
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
                title="Stop audio and reset"
                className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition cursor-pointer"
              >
                <Square className="w-3.5 h-3.5 fill-current text-slate-600" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Spoken Sentence Subtitle during playback */}
      {isPlaying && currentSentenceText && (
        <div className="mt-2.5 pt-2 border-t border-indigo-100/60 flex items-start gap-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-500 bg-indigo-50 px-1.5 py-0.5 rounded flex-shrink-0">
            Speaking
          </span>
          <p className="text-xs text-slate-700 italic line-clamp-2">
            &ldquo;{currentSentenceText}&rdquo;
          </p>
        </div>
      )}
    </div>
  );
}
