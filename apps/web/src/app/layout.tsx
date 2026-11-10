import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "KannadaNewsAI - AI-Powered Kannada-to-English News Translation",
  description: "End-to-end verified machine translation and grounded summarization pipeline for Kannada news.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
        <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
          <p className="max-w-3xl mx-auto">
            KannadaNewsAI • Machine translation powered by IndicTrans2 • AI summaries verified with 7-layer factual checking.
            <br />
            Research demonstration for Academic Evaluation. Outlets terms and robots.txt respected.
          </p>
        </footer>
      </body>
    </html>
  );
}
