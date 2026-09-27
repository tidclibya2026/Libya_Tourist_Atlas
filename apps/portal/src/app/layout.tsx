import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ø§Ù„Ø£Ø·Ù„Ø³ Ø§Ù„Ø³ÙŠØ§Ø­ÙŠ Ø§Ù„Ø±Ù‚Ù…ÙŠ Ø§Ù„ÙˆØ·Ù†ÙŠ Ø§Ù„Ù„ÙŠØ¨ÙŠ",
  description: "Ø§Ù„Ø¨ÙˆØ§Ø¨Ø© Ø§Ù„ÙˆØ·Ù†ÙŠØ© Ù„Ù„ÙˆØ¬Ù‡Ø§Øª ÙˆØ§Ù„Ø®Ø±Ø§Ø¦Ø· ÙˆØ§Ù„Ø®Ø¯Ù…Ø§Øª ÙˆØ§Ù„Ù…Ø¤Ø´Ø±Ø§Øª Ø§Ù„Ø³ÙŠØ§Ø­ÙŠØ© ÙÙŠ Ù„ÙŠØ¨ÙŠØ§",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ar" dir="rtl"><body>{children}</body></html>;
}
