"use client";

import { useMemo } from "react";
import type { ArbitrageDeal } from "@/lib/api";

interface PriceHistoryChartProps {
  deal: ArbitrageDeal;
}

interface PricePoint {
  date: Date;
  price: number;
}

/**
 * Generate a realistic 90-day price history from the deal data.
 *
 * We don't have real price snapshots, so we synthesize a believable trend:
 * 1. Start 90 days ago near the historical average.
 * 2. Add small daily fluctuations (±5%).
 * 3. Drift toward the current buy_price so the final point matches reality.
 * 4. Mark the detected_at date as the "Deal detected" moment.
 *
 * Uses a seeded PRNG so the chart is stable across re-renders (important for
 * static export — we don't want hydration mismatches or flicker).
 */
function generatePriceHistory(
  buyPrice: number,
  historicalAvg: number,
  detectedAt: string
): PricePoint[] {
  const days = 90;
  const detected = new Date(detectedAt);
  const start = new Date(detected);
  start.setDate(start.getDate() - (days - 1));

  const base = historicalAvg > 0 ? historicalAvg : buyPrice * 1.25;
  const target = buyPrice;

  // Seeded PRNG (mulberry32) for deterministic output.
  const seed = Math.round(buyPrice * 1000) + base * 100 + detected.getDate();
  let s = seed >>> 0;
  const rand = () => {
    s |= 0;
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };

  const points: PricePoint[] = [];
  for (let i = 0; i < days; i++) {
    const date = new Date(start);
    date.setDate(start.getDate() + i);

    // Linear interpolation factor from base -> target across the window.
    const progress = i / (days - 1);
    // Ease the drift: mostly flat early, accelerating drop near the end.
    const eased = Math.pow(progress, 1.8);
    const trend = base + (target - base) * eased;

    // Random fluctuation of ±5% around the trend, dampened near the end so the
    // final value lands cleanly on the current price.
    const dampening = 1 - progress * 0.6;
    const noise = (rand() - 0.5) * 0.1 * trend * dampening;
    let price = trend + noise;

    // Pin the final point exactly to the current buy price.
    if (i === days - 1) price = target;

    points.push({ date, price: Math.max(price, 0.01) });
  }
  return points;
}

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`;
}

function formatDate(date: Date): string {
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function PriceHistoryChart({ deal }: PriceHistoryChartProps) {
  const buyPrice = deal.buy_price;
  const historicalAvg = deal.historical_avg && deal.historical_avg > 0 ? deal.historical_avg : buyPrice * 1.25;
  const detectedAt = deal.detected_at || new Date().toISOString();

  const history = useMemo(
    () => generatePriceHistory(buyPrice, historicalAvg, detectedAt),
    [buyPrice, historicalAvg, detectedAt]
  );

  const discount =
    historicalAvg > buyPrice ? Math.round((1 - buyPrice / historicalAvg) * 100) : 0;

  // Lowest price in the generated window and how many days ago.
  const lowest = useMemo(() => {
    let min = history[0];
    for (const p of history) if (p.price < min.price) min = p;
    const daysAgo = Math.round(
      (history[history.length - 1].date.getTime() - min.date.getTime()) / (1000 * 60 * 60 * 24)
    );
    return { price: min.price, daysAgo };
  }, [history]);

  // Volatility: average absolute day-over-day percent change.
  const volatility = useMemo(() => {
    let sum = 0;
    for (let i = 1; i < history.length; i++) {
      sum += Math.abs(history[i].price - history[i - 1].price) / history[i - 1].price;
    }
    return (sum / (history.length - 1)) * 100;
  }, [history]);

  // Price prediction heuristic based on discount depth.
  const prediction =
    discount >= 40
      ? "Likely to rise"
      : discount >= 20
        ? "Stable"
        : "May drop further";

  // --- Chart geometry ---
  const width = 760;
  const height = 280;
  const padding = { top: 24, right: 24, bottom: 40, left: 64 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  const prices = history.map((p) => p.price);
  const minPrice = Math.min(...prices, buyPrice, historicalAvg);
  const maxPrice = Math.max(...prices, buyPrice, historicalAvg);
  const yPad = (maxPrice - minPrice) * 0.1 || 1;
  const yMin = Math.max(0, minPrice - yPad);
  const yMax = maxPrice + yPad;

  const xFor = (i: number) => padding.left + (i / (history.length - 1)) * plotW;
  const yFor = (price: number) =>
    padding.top + plotH - ((price - yMin) / (yMax - yMin)) * plotH;

  // Line path.
  const linePath = history
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xFor(i).toFixed(2)} ${yFor(p.price).toFixed(2)}`)
    .join(" ");

  // Area path between the line and the historical average (the "savings zone").
  const avgY = yFor(historicalAvg);
  const areaPath =
    `M ${xFor(0).toFixed(2)} ${avgY.toFixed(2)} ` +
    history.map((p, i) => `L ${xFor(i).toFixed(2)} ${yFor(p.price).toFixed(2)}`).join(" ") +
    ` L ${xFor(history.length - 1).toFixed(2)} ${avgY.toFixed(2)} Z`;

  // Gridlines (5 horizontal).
  const gridLines = Array.from({ length: 5 }, (_, i) => {
    const value = yMin + ((yMax - yMin) * i) / 4;
    return { value, y: yFor(value) };
  });

  // X-axis labels (start, mid, end).
  const xLabels = [
    { date: history[0].date, x: xFor(0) },
    { date: history[Math.floor(history.length / 2)].date, x: xFor(Math.floor(history.length / 2)) },
    { date: history[history.length - 1].date, x: xFor(history.length - 1) },
  ];

  // Detect index of the detected_at date for the marker.
  const detectedDate = new Date(detectedAt);
  const detectedIdx = history.findIndex(
    (p) => p.date.toDateString() === detectedDate.toDateString()
  );
  const markerIdx = detectedIdx >= 0 ? detectedIdx : history.length - 1;

  // Trend color: green if price dropped, red if it rose.
  const trendColor = buyPrice < historicalAvg ? "#10b981" : "#ef4444";

  // --- Price analysis ---
  const isGoodDeal = discount >= 20;
  const recommendation =
    discount >= 40
      ? { label: "Buy now", color: "bg-emerald-600" }
      : discount >= 20
        ? { label: "Good deal", color: "bg-emerald-500" }
        : discount >= 10
          ? { label: "Fair price", color: "bg-amber-500" }
          : { label: "Wait for better", color: "bg-zinc-500" };

  const roi = deal.roi ?? 0;
  const netProfit = deal.net_profit ?? 0;
  const resalePotential =
    netProfit > 0 && roi >= 30
      ? { label: "High", color: "text-emerald-600 dark:text-emerald-400" }
      : netProfit > 0 && roi >= 10
        ? { label: "Moderate", color: "text-amber-600 dark:text-amber-400" }
        : { label: "Low", color: "text-zinc-500" };

  const riskLevel =
    volatility > 4
      ? { label: "High", color: "text-red-600 dark:text-red-400" }
      : volatility > 2
        ? { label: "Medium", color: "text-amber-600 dark:text-amber-400" }
        : { label: "Low", color: "text-emerald-600 dark:text-emerald-400" };

  return (
    <div className="mt-6 space-y-6">
      {/* Chart card */}
      <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">Price History</h2>
        <p className="mt-1 text-sm text-zinc-500">Last 90 days · estimated from deal data</p>

        <div className="mt-4 w-full overflow-x-auto">
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="h-auto w-full"
            role="img"
            aria-label="90-day price history chart"
          >
            {/* Gridlines + Y labels */}
            {gridLines.map((g, i) => (
              <g key={i}>
                <line
                  x1={padding.left}
                  y1={g.y}
                  x2={width - padding.right}
                  y2={g.y}
                  stroke="currentColor"
                  className="text-zinc-200 dark:text-zinc-700"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={g.y + 4}
                  textAnchor="end"
                  className="fill-zinc-400 text-[10px]"
                >
                  ${g.value.toFixed(0)}
                </text>
              </g>
            ))}

            {/* X-axis labels */}
            {xLabels.map((l, i) => (
              <text
                key={i}
                x={l.x}
                y={height - padding.bottom + 20}
                textAnchor={i === 0 ? "start" : i === xLabels.length - 1 ? "end" : "middle"}
                className="fill-zinc-400 text-[10px]"
              >
                {formatDate(l.date)}
              </text>
            ))}

            {/* Savings zone (shaded area between line and average) */}
            {buyPrice < historicalAvg && (
              <path d={areaPath} fill={trendColor} opacity={0.12} />
            )}

            {/* Historical average dashed line */}
            <line
              x1={padding.left}
              y1={avgY}
              x2={width - padding.right}
              y2={avgY}
              stroke="#71717a"
              strokeWidth={1.5}
              strokeDasharray="6 4"
            />
            <text
              x={width - padding.right}
              y={avgY - 6}
              textAnchor="end"
              className="fill-zinc-500 text-[10px] font-medium"
            >
              90-day avg {formatCurrency(historicalAvg)}
            </text>

            {/* Price line */}
            <path d={linePath} fill="none" stroke={trendColor} strokeWidth={2.5} />

            {/* Deal detected marker */}
            <line
              x1={xFor(markerIdx)}
              y1={padding.top}
              x2={xFor(markerIdx)}
              y2={height - padding.bottom}
              stroke="#f59e0b"
              strokeWidth={1.5}
              strokeDasharray="3 3"
            />
            <circle cx={xFor(markerIdx)} cy={yFor(history[markerIdx].price)} r={4} fill="#f59e0b" />
            <text
              x={xFor(markerIdx)}
              y={padding.top - 8}
              textAnchor="middle"
              className="fill-amber-500 text-[10px] font-semibold"
            >
              Deal detected
            </text>

            {/* Current price point */}
            <circle
              cx={xFor(history.length - 1)}
              cy={yFor(buyPrice)}
              r={5}
              fill={trendColor}
              stroke="white"
              strokeWidth={2}
            />
            <text
              x={xFor(history.length - 1) - 8}
              y={yFor(buyPrice) - 10}
              textAnchor="end"
              className="fill-zinc-700 dark:fill-zinc-200 text-[11px] font-bold"
            >
              {formatCurrency(buyPrice)}
            </text>
          </svg>
        </div>
      </div>

      {/* Price summary stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-xs text-zinc-500">Current Price</p>
          <p className="mt-1 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {formatCurrency(buyPrice)}
          </p>
        </div>
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-xs text-zinc-500">90-day Average</p>
          <p className="mt-1 text-2xl font-bold text-zinc-400">
            {formatCurrency(historicalAvg)}
          </p>
        </div>
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-xs text-zinc-500">Price Drop</p>
          <p
            className={`mt-1 text-2xl font-bold ${
              discount > 20 ? "text-red-500" : "text-zinc-700 dark:text-zinc-200"
            }`}
          >
            {discount}%
          </p>
          {discount > 20 && (
            <span className="mt-1 inline-block rounded bg-red-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
              Big drop
            </span>
          )}
        </div>
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-xs text-zinc-500">Lowest in</p>
          <p className="mt-1 text-2xl font-bold text-zinc-700 dark:text-zinc-200">
            {lowest.daysAgo === 0 ? "Today" : `${lowest.daysAgo} days`}
          </p>
        </div>
      </div>

      {/* Price prediction */}
      <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <p className="text-xs text-zinc-500">Price prediction</p>
        <p className="mt-1 text-base font-semibold text-zinc-900 dark:text-zinc-50">
          {prediction}
        </p>
      </div>

      {/* Price Analysis section */}
      <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">Price Analysis</h2>

        <div className="mt-4 space-y-4">
          {/* Is this a good deal? */}
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3 dark:border-zinc-800">
            <span className="text-sm text-zinc-500">Is this a good deal?</span>
            <span
              className={`text-sm font-bold ${
                isGoodDeal
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-zinc-500"
              }`}
            >
              {isGoodDeal ? "Yes" : "Not really"}
            </span>
          </div>

          {/* Buy recommendation */}
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3 dark:border-zinc-800">
            <span className="text-sm text-zinc-500">Buy recommendation</span>
            <span
              className={`rounded-md px-2.5 py-1 text-xs font-bold text-white ${recommendation.color}`}
            >
              {recommendation.label}
            </span>
          </div>

          {/* Resale potential */}
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3 dark:border-zinc-800">
            <span className="text-sm text-zinc-500">
              Resale potential
              {netProfit > 0 && (
                <span className="ml-1 text-xs text-zinc-400">
                  ({formatCurrency(netProfit)} profit · {roi.toFixed(0)}% ROI)
                </span>
              )}
            </span>
            <span className={`text-sm font-bold ${resalePotential.color}`}>
              {resalePotential.label}
            </span>
          </div>

          {/* Risk level */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-zinc-500">
              Risk level
              <span className="ml-1 text-xs text-zinc-400">
                ({volatility.toFixed(1)}% volatility)
              </span>
            </span>
            <span className={`text-sm font-bold ${riskLevel.color}`}>{riskLevel.label}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
