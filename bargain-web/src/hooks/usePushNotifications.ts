"use client";

import { useState, useEffect, useCallback } from "react";
import { initMessaging, requestNotificationPermission, getFCMToken, onMessageListener } from "@/lib/firebase";
import { authService } from "@/lib/authService";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.bargainhuntrs.com";

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
    const authData = authService.getStoredAuth();
    if (!authData?.access_token) return false;

    try {
      const res = await fetch(`${API_URL}/api/v1/notifications/push/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authData.access_token}`,
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
    const authData = authService.getStoredAuth();
    if (!authData?.access_token) return;

    try {
      await fetch(`${API_URL}/api/v1/notifications/push/unregister`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${authData.access_token}`,
        },
      });
      setRegistered(false);
      setToken(null);
    } catch (err) {
      console.error("Failed to disable push:", err);
    }
  }, []);

  const sendTest = useCallback(async () => {
    const authData = authService.getStoredAuth();
    if (!authData?.access_token) return null;

    try {
      const res = await fetch(`${API_URL}/api/v1/notifications/push/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authData.access_token}`,
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
