import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "Prospect AI — Prospecção Comercial Automatizada",
  description: "Plataforma autônoma de prospecção comercial B2B com IA e WhatsApp",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="bg-slate-50 text-slate-900 min-h-screen">
        <div className="flex">
          <Sidebar />
          <div className="flex-1 ml-64 min-h-screen flex flex-col">
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
