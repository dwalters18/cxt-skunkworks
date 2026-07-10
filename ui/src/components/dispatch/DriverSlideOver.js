/**
 * Driver slide-over — the driver's route in stop order with manual progress
 * controls (the dev stand-in for the driver app until the world simulator
 * takes over). Every button here is an API call that emits canonical events;
 * the board updates when those events come back around.
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../base/utils';
import api from '../../api/client';
import { X, Play, MapPin, FlaskConical } from 'lucide-react';

const STOP_CHIP = {
  PENDING: 'bg-foreground/5 text-muted border border-accent',
  ARRIVED: 'bg-info/15 text-info border border-info/30',
  COMPLETED: 'bg-primary/15 text-primary border border-primary/30',
  FAILED: 'bg-danger/15 text-danger border border-danger/30',
};

function fmtTime(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

function StopRow({ stop, isNextOpen, onAdvance, busy }) {
  const navigate = useNavigate();
  return (
    <div className="rounded-xl border border-accent bg-surface-raised p-3">
      <div className="flex items-center gap-2">
        <span className="w-6 h-6 rounded-full bg-foreground/5 border border-accent flex items-center justify-center text-[10px] font-bold text-muted shrink-0">
          {stop.sequence ?? '•'}
        </span>
        <span className={cn('text-[10px] font-semibold px-1.5 py-0.5 rounded',
          stop.kind === 'PICKUP' ? 'bg-primary/10 text-primary' : 'bg-info/10 text-info')}>
          {stop.kind}
        </span>
        <button
          onClick={() => navigate(`/orders/${stop.orderId}`)}
          className="text-xs font-semibold text-foreground hover:text-primary truncate"
        >
          {stop.orderNumber}
        </button>
        <span className={cn('ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0', STOP_CHIP[stop.status])}>
          {stop.status}
        </span>
      </div>
      <div className="mt-1.5 pl-8 text-[11px] text-muted truncate flex items-center gap-1">
        <MapPin className="w-3 h-3 shrink-0" /> {stop.address}
      </div>
      {(stop.arrivedAt || stop.completedAt) && (
        <div className="mt-1 pl-8 text-[10px] text-muted/70">
          {stop.arrivedAt && <>arrived {fmtTime(stop.arrivedAt)}</>}
          {stop.completedAt && <> · completed {fmtTime(stop.completedAt)}</>}
        </div>
      )}
      {isNextOpen && (
        <div className="mt-2 pl-8 flex gap-1.5">
          {stop.status === 'PENDING' && (
            <button
              disabled={busy}
              onClick={() => onAdvance(stop.stopId, 'ARRIVED')}
              className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-info/15 text-info border border-info/30 hover:bg-info/25 disabled:opacity-50"
            >
              Arrive
            </button>
          )}
          {stop.status === 'ARRIVED' && (
            <button
              disabled={busy}
              onClick={() => onAdvance(stop.stopId, 'COMPLETED')}
              className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-primary text-background hover:bg-primary/85 disabled:opacity-50"
            >
              Complete
            </button>
          )}
          {(stop.status === 'PENDING' || stop.status === 'ARRIVED') && (
            <button
              disabled={busy}
              onClick={() => onAdvance(stop.stopId, 'FAILED')}
              className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-danger/10 text-danger border border-danger/30 hover:bg-danger/20 disabled:opacity-50"
            >
              Fail
            </button>
          )}
        </div>
      )}
    </div>
  );
}

const DriverSlideOver = ({ driver, route, onClose }) => {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const advance = async (stopId, status) => {
    setBusy(true);
    setError(null);
    try {
      await api.updateStopStatus(stopId, status);
      // No refetch: the stop.status-updated event updates the board.
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const startRoute = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.startRoute(route.id);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const stops = route ? [...route.stops].sort((a, b) => (a.sequence ?? 0) - (b.sequence ?? 0)) : [];
  const nextOpenIdx = stops.findIndex((s) => s.status === 'PENDING' || s.status === 'ARRIVED');

  return (
    <div className="absolute inset-y-0 right-0 z-50 w-[380px] bg-surface border-l border-accent shadow-card flex flex-col animate-in slide-in-from-right duration-200">
      <div className="px-4 py-3 border-b border-accent flex items-center gap-2">
        <div>
          <h3 className="font-heading font-semibold text-foreground">{driver.name}</h3>
          <div className="text-[11px] text-muted">
            {driver.driverNumber} · {route?.vehicle?.vehicleNumber || 'no vehicle'} ·{' '}
            {route ? `${route.routeNumber} (${route.status})` : 'no open route'}
          </div>
        </div>
        <button onClick={onClose} className="ml-auto p-1.5 rounded-lg hover:bg-foreground/5 text-muted">
          <X className="w-4 h-4" />
        </button>
      </div>

      {route?.status === 'PLANNED' && (
        <div className="px-4 py-3 border-b border-accent">
          <button
            disabled={busy || stops.length === 0 || !route.vehicle}
            onClick={startRoute}
            className="w-full flex items-center justify-center gap-2 text-sm font-semibold px-3 py-2 rounded-xl bg-primary text-background hover:bg-primary/85 disabled:opacity-40"
          >
            <Play className="w-4 h-4" /> Start {route.routeNumber}
          </button>
          {stops.length === 0 && (
            <p className="mt-1.5 text-[11px] text-muted text-center">Assign an order before starting.</p>
          )}
        </div>
      )}

      <div className="px-4 py-2 flex items-center gap-1.5 text-[11px] text-muted border-b border-accent">
        <FlaskConical className="w-3.5 h-3.5 text-warn" />
        Manual stop progress (dev) — the world simulator drives this next.
      </div>

      {error && (
        <div className="mx-4 mt-2 px-3 py-2 text-xs rounded-lg bg-danger/10 text-danger border border-danger/30">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {stops.length === 0 ? (
          <div className="text-center text-xs text-muted py-8">No stops on this driver's plate.</div>
        ) : (
          stops.map((s, i) => (
            <StopRow key={s.stopId} stop={s} isNextOpen={i === nextOpenIdx} onAdvance={advance} busy={busy} />
          ))
        )}
      </div>
    </div>
  );
};

export default DriverSlideOver;
