/**
 * Analytics — honest views over real data only: event throughput by type,
 * per-minute volume, and order/stop outcomes from the summary endpoint.
 * No chart library; bars are plain divs.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { cn } from '../components/base/utils';
import api from '../api/client';
import { eventTone } from './DashboardPage';
import { BarChart3, Activity, Package, MapPin } from 'lucide-react';

const SOURCE_BAR_TONES = {
  'lip-api': 'bg-emerald-500 dark:bg-primary',
  'lip-cdc-normalizer': 'bg-gray-400',
  'lip-simulator': 'bg-violet-500',
  'lip-seeder': 'bg-amber-500',
};

const ORDER_STATUS_BARS = [
  ['created', 'bg-orange-400'],
  ['assigned', 'bg-sky-400'],
  ['in_progress', 'bg-emerald-500 dark:bg-primary'],
  ['completed', 'bg-gray-400'],
  ['cancelled', 'bg-red-400'],
];

const fmtMinute = (iso) => new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

function Card({ icon: Icon, title, subtitle, children }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-5">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4 text-primary" />
        <h2 className="text-sm font-semibold text-gray-900 dark:text-foreground">{title}</h2>
      </div>
      {subtitle && <p className="text-xs text-gray-500 dark:text-muted mb-3">{subtitle}</p>}
      {children}
    </div>
  );
}

function ProportionRow({ label, count, total, barClass }) {
  const pct = total > 0 ? (100 * count) / total : 0;
  return (
    <div className="flex items-center gap-3 text-xs">
      <span className="w-28 shrink-0 text-gray-600 dark:text-muted capitalize">{label.replace('_', ' ')}</span>
      <div className="flex-1 h-2 rounded bg-gray-100 dark:bg-gray-800 overflow-hidden">
        <div className={cn('h-full rounded', barClass)} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 text-right tabular-nums text-gray-900 dark:text-foreground font-medium">{count}</span>
    </div>
  );
}

const AnalyticsPage = () => {
  const [buckets, setBuckets] = useState([]);
  const [volume, setVolume] = useState([]);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  const fetchAll = useCallback(async () => {
    try {
      const [byType, vol, sum] = await Promise.all([
        api.eventsByType(24),
        api.eventVolume(60),
        api.analyticsSummary(),
      ]);
      setBuckets((byType.buckets || []).slice().sort((a, b) => b.count - a.count));
      setVolume(vol.points || []);
      setSummary(sum);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const poll = setInterval(fetchAll, 15000);
    return () => clearInterval(poll);
  }, [fetchAll]);

  const maxBucket = Math.max(1, ...buckets.map((b) => b.count));
  const maxVolume = Math.max(1, ...volume.map((p) => p.count));
  const orders = summary?.orders;
  const stops = summary?.stops;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-foreground">Analytics</h1>
        <p className="text-gray-600 dark:text-muted mt-1">Measured from the backbone and the system of record — nothing synthetic</p>
      </div>

      {error && (
        <div className="px-3 py-2 text-xs rounded bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/30">{error}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card icon={BarChart3} title="Events by type (24h)" subtitle="Bar color groups producers; tag shows the source system">
          {buckets.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-muted">No events in the last 24 hours</p>
          ) : (
            <div className="space-y-2">
              {buckets.map((b) => (
                <div key={`${b.event_type}:${b.source_system}`} className="flex items-center gap-2 text-xs">
                  <span className={cn('w-52 shrink-0 font-mono truncate', eventTone(b.event_type))} title={b.event_type}>
                    {b.event_type}
                  </span>
                  <span className="w-32 shrink-0 rounded text-[10px] px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-muted text-center truncate">
                    {b.source_system}
                  </span>
                  <div className="flex-1 h-2.5 rounded bg-gray-100 dark:bg-gray-800 overflow-hidden">
                    <div
                      className={cn('h-full rounded', SOURCE_BAR_TONES[b.source_system] || 'bg-sky-500')}
                      style={{ width: `${Math.max(2, (100 * b.count) / maxBucket)}%` }}
                    />
                  </div>
                  <span className="w-14 text-right tabular-nums text-gray-900 dark:text-foreground font-medium">
                    {b.count.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card icon={Activity} title="Event volume (last 60 min)" subtitle="Every event on every canonical topic, per minute">
          {volume.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-muted">No events in the last hour</p>
          ) : (
            <>
              <div className="flex items-end gap-px h-28">
                {volume.map((p) => (
                  <div
                    key={p.minute}
                    title={`${fmtMinute(p.minute)} — ${p.count} events`}
                    className="flex-1 rounded-t bg-emerald-500/80 dark:bg-primary/70 hover:bg-emerald-500 dark:hover:bg-primary min-w-0"
                    style={{ height: `${Math.max(3, (100 * p.count) / maxVolume)}%` }}
                  />
                ))}
              </div>
              <div className="mt-2 flex justify-between text-[10px] text-gray-500 dark:text-muted">
                <span>{fmtMinute(volume[0].minute)}</span>
                <span>peak {maxVolume.toLocaleString()}/min</span>
                <span>{fmtMinute(volume[volume.length - 1].minute)}</span>
              </div>
            </>
          )}
        </Card>

        <Card icon={Package} title="Order status distribution" subtitle={orders ? `${orders.total} orders in the world model` : undefined}>
          {!orders ? (
            <p className="text-sm text-gray-500 dark:text-muted">Loading…</p>
          ) : (
            <div className="space-y-2">
              {ORDER_STATUS_BARS.map(([key, barClass]) => (
                <ProportionRow key={key} label={key} count={orders[key] || 0} total={orders.total} barClass={barClass} />
              ))}
            </div>
          )}
        </Card>

        <Card icon={MapPin} title="Stop completion" subtitle="Service-window performance across all stops">
          {!stops ? (
            <p className="text-sm text-gray-500 dark:text-muted">Loading…</p>
          ) : (
            <div className="space-y-2">
              <ProportionRow label="completed" count={stops.completed} total={stops.total} barClass="bg-emerald-500 dark:bg-primary" />
              <ProportionRow label="in window" count={stops.completed_in_window} total={stops.total} barClass="bg-sky-400" />
              <div className="pt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-gray-900 dark:text-foreground">
                  {stops.onTimePercentage == null ? '—' : `${Math.round(stops.onTimePercentage)}%`}
                </span>
                <span className="text-xs text-gray-500 dark:text-muted">
                  on-time · {stops.completed_in_window} of {stops.completed} completed stops inside their window
                </span>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default AnalyticsPage;
