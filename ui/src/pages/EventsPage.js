/**
 * Canonical Event Console — the contract showcase.
 *
 * Every producer (API, CDC normalizer, simulator, seeder) speaks the same
 * envelope v1. This page tails the backbone live, lets you inspect any
 * envelope verbatim, and demonstrates publish-side validation: a malformed
 * event is rejected with a 422 and never reaches Kafka.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { cn } from '../components/base/utils';
import { useWebSocket } from '../contexts/WebSocketContext';
import api from '../api/client';
import { eventTone, summarizeEvent } from './DashboardPage';
import { Radio, Send, FlaskConical, CheckCircle2, XCircle, EyeOff } from 'lucide-react';

const NAMESPACES = [
  { id: 'all', label: 'All', match: () => true },
  { id: 'orders', label: 'Orders', match: (t) => t.startsWith('order.') && !t.includes('.record-') },
  { id: 'stops', label: 'Stops', match: (t) => t.startsWith('stop.') && !t.includes('.record-') },
  { id: 'routes', label: 'Routes', match: (t) => t.startsWith('route.') && !t.includes('.record-') },
  { id: 'drivers', label: 'Drivers', match: (t) => t.startsWith('driver.') && !t.includes('.record-') },
  { id: 'vehicles', label: 'Vehicles', match: (t) => t.startsWith('vehicle.') && !t.includes('.record-') },
  { id: 'cdc', label: 'CDC', match: (t) => t.includes('.record-') },
  { id: 'system', label: 'System', match: (t) => t.startsWith('system.') },
];

const SOURCES = ['all', 'lip-api', 'lip-cdc-normalizer', 'lip-simulator', 'lip-seeder'];

const VALID_EXAMPLE = {
  eventType: 'order.cancelled',
  entityRefs: [{ type: 'order', id: 'b1000000-0000-4000-8000-000000000030' }],
  payload: {
    orderId: 'b1000000-0000-4000-8000-000000000030',
    orderNumber: 'ORD-1030',
    reason: 'Console test',
  },
};

const INVALID_EXAMPLE = {
  eventType: 'order.exploded',
  entityRefs: [{ type: 'order', id: 'x' }],
  payload: {},
};

const fmtClock = (iso) =>
  iso ? new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }) : '';

function EventRow({ envelope, expanded, onToggle }) {
  const ref = envelope.entityRefs?.[0];
  return (
    <div className="border-b border-gray-100 dark:border-gray-800">
      <button onClick={onToggle} className="w-full text-left px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-800/50">
        <div className="flex items-center gap-3 text-xs min-w-0">
          <span className="font-mono text-gray-400 dark:text-muted w-16 shrink-0">{fmtClock(envelope.observedAt)}</span>
          <span className={cn('font-mono font-semibold w-52 shrink-0 truncate', eventTone(envelope.eventType))}>
            {envelope.eventType}
          </span>
          <span className="shrink-0 rounded text-[10px] px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-muted">
            {envelope.sourceSystem}
          </span>
          {ref && (
            <span className="font-mono text-gray-500 dark:text-muted shrink-0 hidden sm:inline">
              {ref.type}:{String(ref.id).slice(0, 8)}
            </span>
          )}
          <span className="text-gray-600 dark:text-muted truncate">{summarizeEvent(envelope)}</span>
        </div>
      </button>
      {expanded && (
        <pre className="mx-4 mb-3 p-3 rounded-md bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-accent text-[11px] leading-relaxed font-mono text-gray-800 dark:text-foreground overflow-x-auto">
          {JSON.stringify(envelope, null, 2)}
        </pre>
      )}
    </div>
  );
}

function PublishPanel() {
  const [draft, setDraft] = useState(JSON.stringify(VALID_EXAMPLE, null, 2));
  const [result, setResult] = useState(null);
  const [publishing, setPublishing] = useState(false);

  const handlePublish = async () => {
    setResult(null);
    let body;
    try {
      body = JSON.parse(draft);
    } catch (e) {
      setResult({ ok: false, message: `Not valid JSON: ${e.message}` });
      return;
    }
    setPublishing(true);
    try {
      const res = await api.publishEvent(body);
      setResult({ ok: true, eventId: res.eventId, topic: res.topic });
    } catch (e) {
      setResult({ ok: false, status: e.status, message: e.message });
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-5 h-fit xl:sticky xl:top-6">
      <div className="flex items-center gap-2 mb-1">
        <Send className="w-4 h-4 text-primary" />
        <h2 className="text-sm font-semibold text-gray-900 dark:text-foreground">Publish test event</h2>
      </div>
      <p className="text-xs text-gray-500 dark:text-muted mb-3">
        The publisher validates the envelope and the per-type payload schema before anything reaches Kafka.
      </p>

      <textarea
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        rows={13}
        spellCheck={false}
        className="w-full font-mono text-[11px] leading-relaxed p-3 rounded-md border border-gray-200 dark:border-accent bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-y"
      />

      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={handlePublish}
          disabled={publishing}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-md bg-primary text-background hover:bg-primary/80 disabled:opacity-50"
        >
          <Send className="w-3.5 h-3.5" /> {publishing ? 'Publishing…' : 'Publish'}
        </button>
        <button
          onClick={() => {
            setDraft(JSON.stringify(INVALID_EXAMPLE, null, 2));
            setResult(null);
          }}
          className="flex items-center gap-1.5 px-3 py-2 text-sm font-semibold rounded-md border border-gray-200 dark:border-accent text-gray-700 dark:text-foreground hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <FlaskConical className="w-3.5 h-3.5 text-amber-500" /> Try an invalid event
        </button>
      </div>

      {result && result.ok && (
        <div className="mt-3 px-3 py-2 rounded-md bg-green-500/10 border border-green-500/30 text-xs text-green-700 dark:text-green-400">
          <div className="flex items-center gap-1.5 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" /> Accepted onto the backbone
          </div>
          <div className="mt-1 font-mono break-all">eventId {result.eventId}</div>
          <div className="font-mono">topic {result.topic}</div>
        </div>
      )}
      {result && !result.ok && (
        <div className="mt-3 px-3 py-2 rounded-md bg-red-500/10 border border-red-500/30 text-xs text-red-600 dark:text-red-400">
          <div className="flex items-center gap-1.5 font-semibold">
            <XCircle className="w-3.5 h-3.5" /> {result.status === 422 ? 'Rejected (422)' : 'Publish failed'}
          </div>
          <div className="mt-1 font-mono break-all whitespace-pre-wrap">{result.message}</div>
          {result.status === 422 && (
            <div className="mt-1.5 text-red-500 dark:text-red-300">
              rejected at publish time — malformed events never reach the backbone
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const EventsPage = () => {
  const { isConnected, addEventListener } = useWebSocket();
  const [events, setEvents] = useState([]);
  const [namespace, setNamespace] = useState('all');
  const [source, setSource] = useState('all');
  const [hideTelemetry, setHideTelemetry] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [error, setError] = useState(null);

  const mergeEvents = useCallback((incoming) => {
    setEvents((prev) => {
      const seen = new Set(prev.map((e) => e.eventId));
      return [...prev, ...incoming.filter((e) => !seen.has(e.eventId))].slice(0, 200);
    });
  }, []);

  useEffect(() => {
    api
      .recentEvents({ limit: 50 })
      .then((res) => mergeEvents(res.events || []))
      .catch((e) => setError(e.message));
  }, [mergeEvents]);

  useEffect(() => {
    const unsubscribe = addEventListener((envelope) => {
      setEvents((prev) =>
        prev.some((e) => e.eventId === envelope.eventId) ? prev : [envelope, ...prev].slice(0, 200)
      );
    });
    return unsubscribe;
  }, [addEventListener]);

  const nsMatch = NAMESPACES.find((n) => n.id === namespace) || NAMESPACES[0];
  const visible = events.filter(
    (e) =>
      nsMatch.match(e.eventType) &&
      (source === 'all' || e.sourceSystem === source) &&
      (!hideTelemetry || e.eventType !== 'driver.location-updated')
  );

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-foreground">Canonical Event Console</h1>
          <span
            title={isConnected ? 'live feed connected' : 'feed disconnected'}
            className={cn('w-2.5 h-2.5 rounded-full', isConnected ? 'bg-primary animate-pulse' : 'bg-red-500')}
          />
        </div>
        <p className="text-gray-600 dark:text-muted mt-1">
          Every event on the backbone uses envelope v1 — one contract, four producers.
        </p>
      </div>

      {error && (
        <div className="px-3 py-2 text-xs rounded bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/30">{error}</div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_380px] gap-6 items-start">
        <div className="space-y-3 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            {NAMESPACES.map((n) => (
              <button
                key={n.id}
                onClick={() => setNamespace(n.id)}
                className={cn(
                  'rounded-full text-xs px-3 py-1 font-semibold transition-colors',
                  namespace === n.id
                    ? 'bg-primary text-background'
                    : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-accent text-gray-600 dark:text-muted hover:bg-gray-100 dark:hover:bg-gray-800'
                )}
              >
                {n.label}
              </button>
            ))}
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="ml-auto text-xs px-2 py-1.5 rounded-md border border-gray-200 dark:border-accent bg-white dark:bg-gray-900 text-gray-700 dark:text-foreground"
            >
              {SOURCES.map((s) => (
                <option key={s} value={s}>
                  {s === 'all' ? 'all sources' : s}
                </option>
              ))}
            </select>
            <button
              onClick={() => setHideTelemetry((h) => !h)}
              className={cn(
                'flex items-center gap-1.5 rounded-full text-xs px-3 py-1 font-semibold transition-colors',
                hideTelemetry
                  ? 'bg-violet-500/15 text-violet-600 dark:text-violet-400'
                  : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-accent text-gray-600 dark:text-muted hover:bg-gray-100 dark:hover:bg-gray-800'
              )}
              title="driver.location-updated is high-volume GPS telemetry"
            >
              <EyeOff className="w-3.5 h-3.5" /> {hideTelemetry ? 'Location telemetry hidden' : 'Hide location telemetry'}
            </button>
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-200 dark:border-accent text-xs text-gray-500 dark:text-muted">
              <Radio className="w-3.5 h-3.5 text-primary" />
              showing {visible.length} of {events.length} buffered envelopes · click a row for the full envelope
            </div>
            <div className="max-h-[70vh] overflow-y-auto">
              {visible.length === 0 ? (
                <div className="px-4 py-10 text-center text-sm text-gray-500 dark:text-muted">
                  No events match these filters yet
                </div>
              ) : (
                visible.map((envelope) => (
                  <EventRow
                    key={envelope.eventId}
                    envelope={envelope}
                    expanded={expandedId === envelope.eventId}
                    onToggle={() => setExpandedId(expandedId === envelope.eventId ? null : envelope.eventId)}
                  />
                ))
              )}
            </div>
          </div>
        </div>

        <PublishPanel />
      </div>
    </div>
  );
};

export default EventsPage;
