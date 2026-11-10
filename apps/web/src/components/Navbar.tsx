"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Search, PlusCircle, BookOpen, BarChart2, Bookmark, Globe } from "lucide-react";

export default function Navbar() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-b border-slate-200 dark:border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 group flex-shrink-0">
          <div className="w-9 h-9 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-lg shadow-sm group-hover:bg-indigo-700 transition">
            ಕ
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-base tracking-tight text-slate-900 dark:text-white flex items-center gap-1.5">
              KannadaNews<span className="text-indigo-600">AI</span>
            </span>
            <span className="text-[10px] text-slate-500 font-kannada leading-none">
              ಕನ್ನಡ ಸುದ್ದಿ ಅನುವಾದ ಮತ್ತು ಸಾರಾಂಶ
            </span>
          </div>
        </Link>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex-1 max-w-md relative hidden md:block">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search news in English or ಕನ್ನಡ..."
            className="w-full pl-9 pr-4 py-1.5 text-sm bg-slate-100 dark:bg-slate-800 border-none rounded-full focus:ring-2 focus:ring-indigo-500 focus:outline-none placeholder-slate-400 text-slate-800 dark:text-slate-100"
          />
        </form>

        {/* Navigation & CTAs */}
        <nav className="flex items-center gap-1 sm:gap-3">
          <Link
            href="/kannada"
            className="px-3 py-1.5 text-xs sm:text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-indigo-600 rounded-md transition flex items-center gap-1.5 font-kannada"
          >
            <Globe className="w-4 h-4 text-slate-400" />
            ಕನ್ನಡ ಫೀಡ್
          </Link>
          <Link
            href="/english"
            className="px-3 py-1.5 text-xs sm:text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-indigo-600 rounded-md transition flex items-center gap-1.5"
          >
            English Feed
          </Link>
          <Link
            href="/history"
            className="px-2.5 py-1.5 text-slate-600 dark:text-slate-300 hover:text-indigo-600 rounded-md transition"
            title="Reading History & Bookmarks"
          >
            <Bookmark className="w-4 h-4" />
          </Link>
          <Link
            href="/insights"
            className="px-2.5 py-1.5 text-slate-600 dark:text-slate-300 hover:text-indigo-600 rounded-md transition"
            title="System Insights & Evaluation"
          >
            <BarChart2 className="w-4 h-4" />
          </Link>

          <Link
            href="/submit"
            className="ml-2 inline-flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs sm:text-sm font-medium px-3.5 py-1.5 rounded-full shadow-sm transition"
          >
            <PlusCircle className="w-4 h-4" />
            Submit Article
          </Link>
        </nav>
      </div>
    </header>
  );
}
