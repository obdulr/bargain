"use client";

import { useEffect, useState } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const STORAGE_KEY = "pwa-install-dismissed";

export default function PwaInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const dismissed = window.localStorage.getItem(STORAGE_KEY);
    if (dismissed) return;

    const handleBeforeInstallPrompt = (event: Event) => {
      event.preventDefault();
      setDeferredPrompt(event as BeforeInstallPromptEvent);
      setIsVisible(true);
    };

    const handleAppInstalled = () => {
      setDeferredPrompt(null);
      setIsVisible(false);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === "accepted") {
      setDeferredPrompt(null);
      setIsVisible(false);
    }
  };

  const handleDismiss = () => {
    setIsVisible(false);
    window.localStorage.setItem(STORAGE_KEY, "true");
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4">
      <div className="mx-auto max-w-md rounded-2xl border border-zinc-800 bg-zinc-900/95 p-4 shadow-2xl backdrop-blur-sm">
        <div className="flex items-start gap-4">
          <div className="shrink-0">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/icons/icon-72x72.png"
              alt="Bargain Huntrs"
              className="h-12 w-12 rounded-xl"
            />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-white">Install Bargain Huntrs</h3>
            <p className="mt-1 text-xs text-zinc-400">
              Add Bargain Huntrs to your home screen for quick access to deals and price drops.
            </p>
          </div>
          <button
            onClick={handleDismiss}
            aria-label="Dismiss install prompt"
            className="shrink-0 text-zinc-500 transition-colors hover:text-white"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="h-5 w-5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={handleDismiss}
            className="rounded-lg px-4 py-2 text-xs font-medium text-zinc-400 transition-colors hover:text-white"
          >
            Not now
          </button>
          <button
            onClick={handleInstall}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-emerald-600"
          >
            Install
          </button>
        </div>
      </div>
    </div>
  );
}
