import Script from "next/script";

const GA_ID = process.env.NEXT_PUBLIC_GA4_ID || "";

/**
 * Google Analytics 4 (gtag.js) loader.
 *
 * Renders nothing when NEXT_PUBLIC_GA4_ID is unset/empty so dev and
 * unconfigured environments stay analytics-free.
 */
export default function GoogleAnalytics() {
  if (!GA_ID) return null;

  return (
    <>
      <Script
        id="ga4-gtag-src"
        strategy="afterInteractive"
        src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
      />
      <Script
        id="ga4-gtag-init"
        strategy="afterInteractive"
        dangerouslySetInnerHTML={{
          __html: `window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', '${GA_ID}', { page_path: window.location.pathname });`,
        }}
      />
    </>
  );
}
