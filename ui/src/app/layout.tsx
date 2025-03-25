import "@/src/styles/globals.css";
import { Metadata, Viewport } from "next";
import clsx from "clsx";
import { Providers } from "../providers/root";
import { siteConfig } from "@/src/config/site";
import { fontSans } from "@/src/config/fonts";
import NextTopLoader from "nextjs-toploader";

export const metadata: Metadata = {
  title: {
    default: siteConfig.title,
    template: `%s - ${siteConfig.title}`,
  },
  description: siteConfig.description,
  icons: {
    icon: "/favicon.ico",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "white" },
    { media: "(prefers-color-scheme: dark)", color: "black" },
  ],
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head />
      <body
        className={clsx(
          "min-h-screen bg-background font-sans antialiased",
          fontSans.variable
        )}
      >
        <NextTopLoader />
        <Providers themeProps={{ attribute: "class", defaultTheme: "dark" }}>
          <main className="h-screen w-full flex items-center justify-center">
            <div className="w-full sm:max-w-4xl md:max-w-5xl rounded-lg">
              {children}
            </div>
          </main>
        </Providers>
      </body>
    </html>
  );
}
