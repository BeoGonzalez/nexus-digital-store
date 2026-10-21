import type { Metadata, Viewport } from "next";
import { Outfit, JetBrains_Mono } from "next/font/google";
import { QueryProvider } from "@/presentation/providers/QueryProvider";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Gamma Game Store — Videojuegos premium",
  description:
    "Descubre nuevos lanzamientos y encuentra tu próximo videojuego con Gamma Game Store.",
  generator: "v0.app",
};

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#101214",
  userScalable: false,
};

import { GammaBackground } from "@/presentation/components/background/GammaBackground";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <body
        className={`${outfit.variable} ${jetbrainsMono.variable} ${outfit.className} antialiased bg-transparent text-zinc-100 selection:bg-cyan-500 selection:text-zinc-950 flex flex-col min-h-screen relative`}
      >
        <GammaBackground />
        <QueryProvider>
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}
