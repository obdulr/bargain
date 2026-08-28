"use client";

import { useState, useEffect, useCallback } from "react";
import { initMessaging, requestNotificationPermission, getFCMToken, onMessageListener } from "@/lib/firebase";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.bargainhuntrs.com";

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("bargain_auth_token");
}

export function usePushNotifications() {
  const [permission, setPermission] = useState<NotificationPermission>("default");
  const [token, setToken] = useState<string | null>(null);
  const [registered, setRegistered] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window) {
      setPermission(Notification.permission);
    }
  }, []);

  const registerToken = useCallback(async (fcmToken: string) => {
    const authToken = getAuthToken();
    if (!authToken) return false;

    try {
      const res = await fetch(`${API_URL}/api/v1/notifications/push/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ token: fcmToken }),
      });

      if (res.ok) {
        setRegistered(true);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }, []);

  const enable = useCallback(async () => {
    setLoading(true);
    try {
      const perm = await requestNotificationPermission();
      setPermission(perm);
      if (perm !== "granted") return false;

      await initMessaging();
      const fcmToken = await getFCMToken();
      if (!fcmToken) return false;

      setToken(fcmToken);
      const success = await registerToken(fcmToken);
      return success;
    } catch (err) {
      console.error("Failed to enable push notifications:", err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [registerToken]);

  const disable = useCallback(async () => {
    const authToken = getAuthToken();
    if (!authToken) return;

    try {
      await fetch(`${API_URL}/api/v1/notifications/push/unregister`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });
      setRegistered(false);
      setToken(null);
    } catch (err) {
      console.error("Failed to disable push:", err);
    }
  }, []);

  const sendTest = useCallback(async () => {
    const authToken = getAuthToken();
    if (!authToken) return null;

    try {
      const res = await fetch(`${API_URL}/api/v1/notifications/push/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          title: "🔥 Test Deal Alert",
          body: "Push notifications are working! You'll be notified of hot deals.",
        }),
      });
      return await res.json();
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    onMessageListener((payload: any) => {
      if (payload?.notification) {
        const { title, body } = payload.notification;
        if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
          new Notification(title, {
            body,
            icon: "/icon-192.png",
            badge: "/icon-72.png",
            data: payload.data,
          });
        }
      }
    });
  }, []);

  return {
    permission,
    token,
    registered,
    loading,
    enable,
    disable,
    sendTest,
  };
}
