import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FormFix AI – Real-Time Posture Correction",
  description: "AI-powered exercise and yoga posture correction using your webcam",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
