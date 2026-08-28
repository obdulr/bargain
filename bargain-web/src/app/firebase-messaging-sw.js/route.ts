export const dynamic = "force-static";
export const revalidate = false;

const swCode = `
importScripts("https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js");

const firebaseConfig = {
  apiKey: "AIzaSyDWt8Zk1t0mjmDOP0QszVBbPG2a4Tnnx58",
  projectId: "bargainhuntrs-a57ec",
  messagingSenderId: "809115335784",
  appId: "1:809115335784:web:a41b07b345655901498fdd",
};

if (typeof firebase !== "undefined") {
  firebase.initializeApp(firebaseConfig);
  const messaging = firebase.messaging();

  messaging.onBackgroundMessage((payload) => {
    const notificationTitle = payload.notification?.title || "BargainHuntrs";
    const notificationOptions = {
      body: payload.notification?.body || "",
      icon: "/icon-192.png",
      badge: "/icon-72.png",
      data: payload.data || {},
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
  });

  self.addEventListener("notificationclick", (event) => {
    event.notification.close();
    const url = event.notification.data?.url || "/deals";
    event.waitUntil(
      clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
        for (const client of clientList) {
          if ("focus" in client) {
            client.navigate(url);
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
    );
  });
}
`;

export function GET() {
  return new Response(swCode, {
    headers: {
      "Content-Type": "application/javascript; charset=utf-8",
      "Cache-Control": "no-cache, no-store, must-revalidate",
      "Service-Worker-Allowed": "/",
    },
  });
}
