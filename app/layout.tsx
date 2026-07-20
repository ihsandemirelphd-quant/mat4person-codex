import type { Metadata } from "next";
import { headers } from "next/headers";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost:3000";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? (host.startsWith("localhost") ? "http" : "https");
  const origin = `${protocol}://${host}`;
  return {
    title: "MAT4Person — Evidence-first relationship atlas",
    description: "A Codex plugin and reproducible pipeline that turns source documents into independently verified relationship graphs.",
    openGraph: {
      title: "MAT4Person — Every edge shows its receipts",
      description: "Source-grounded relationship research with Codex and GPT-5.6.",
      type: "website",
      url: origin,
      images: [{ url: `${origin}/og.png`, width: 1200, height: 630, alt: "MAT4Person evidence-first relationship atlas" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "MAT4Person — Every edge shows its receipts",
      description: "Source-grounded relationship research with Codex and GPT-5.6.",
      images: [`${origin}/og.png`],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>{children}</body>
    </html>
  );
}
