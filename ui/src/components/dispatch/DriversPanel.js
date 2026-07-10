/**
 * Drivers & routes panel — one row per driver: duty status, vehicle, current
 * route and load. Rows accept order drops (and clicks while an order is
 * selected) to dispatch work; clicking a row otherwise opens the slide-over.
 */
import React, { useState } from 'react';
import { cn } from '../base/utils';
import { routeColor } from '../map/MapContainer';
import { Users, Truck, CircleDot } from 'lucide-react';

const DUTY_CHIP = {
  AVAILABLE: 'bg-primary/15 text-primary border border-primary/30',
  ON_ROUTE: 'bg-info/15 text-info border border-info/30',
  OFF_DUTY: 'bg-foreground/5 text-muted border border-accent',
};

function initials(name = '') {
  return name
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

function DriverRow({ driver, routeIndex, canReceive, onAssign, onOpen }) {
  const [dragOver, setDragOver] = useState(false);
  const r = driver.currentRoute;
  const color = r ? routeColor(routeIndex) : '#4B5563';
  const offDuty = driver.status === 'OFF_DUTY';
  const receivable = canReceive && !offDuty;

  return (
    <div
      onDragOver={(e) => {
        if (!offDuty) {
          e.preventDefault();
          setDragOver(true);
        }
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        setDragOver(false);
        const orderId = e.dataTransfer.getData('text/lip-order-id');
        if (orderId && !offDuty) onAssign(orderId, driver.id);
      }}
      onClick={() => (receivable ? onAssign(null, driver.id) : onOpen(driver.id))}
      className={cn(
        'rounded-card border p-3 transition-all cursor-pointer select-none',
        dragOver
          ? 'border-primary bg-primary/15 scale-[1.01]'
          : receivable
          ? 'border-primary/50 bg-primary/5 hover:bg-primary/10'
          : 'border-accent bg-surface-raised hover:border-primary/30',
        offDuty && 'opacity-50'
      )}
    >
      <div className="flex items-center gap-2.5">
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold text-background shrink-0"
          style={{ backgroundColor: r ? color : '#96A19B' }}
        >
          {initials(driver.name)}
        </div>
        <div className="min-w-0">
          <div className="font-heading font-semibold text-sm text-foreground truncate">{driver.name}</div>
          <div className="text-[11px] text-muted flex items-center gap-1.5">
            <Truck className="w-3 h-3" />
            {r?.vehicle?.vehicleNumber || 'no vehicle'}
          </div>
        </div>
        <span className={cn('ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0', DUTY_CHIP[driver.status])}>
          {driver.status.replace('_', ' ')}
        </span>
      </div>

      {r ? (
        <div className="mt-2 pl-10">
          <div className="flex items-center gap-2 text-[11px]">
            <span className="font-semibold" style={{ color }}>{r.routeNumber}</span>
            <span className={cn('px-1.5 py-0.5 rounded-full text-[9px] font-semibold',
              r.status === 'ACTIVE' ? 'bg-primary/15 text-primary' : 'bg-info/15 text-info')}>
              {r.status}
            </span>
            <span className="ml-auto text-muted">
              {r.openStops} open · {r.stopsCompleted}/{r.stopsTotal} done
            </span>
          </div>
          <div className="mt-1.5 h-1 rounded bg-foreground/5 overflow-hidden">
            <div
              className="h-full rounded transition-all duration-500"
              style={{
                width: `${r.stopsTotal ? (100 * r.stopsCompleted) / r.stopsTotal : 0}%`,
                backgroundColor: color,
              }}
            />
          </div>
        </div>
      ) : (
        <div className="mt-2 pl-10 text-[11px] text-muted/70">
          {offDuty ? 'off duty' : 'no route yet — assigning plans one automatically'}
        </div>
      )}

      {receivable && (
        <div className="mt-2 pl-10 text-[11px] font-semibold text-primary flex items-center gap-1">
          <CircleDot className="w-3 h-3" /> assign selected order here
        </div>
      )}
    </div>
  );
}

const DriversPanel = ({ drivers, routeIndexById, selectedOrderId, onAssign, onOpenDriver }) => {
  const onDutyFirst = [...drivers].sort((a, b) => {
    const rank = (d) => (d.status === 'ON_ROUTE' ? 0 : d.status === 'AVAILABLE' ? 1 : 2);
    return rank(a) - rank(b) || a.name.localeCompare(b.name);
  });

  return (
    <aside className="w-[340px] shrink-0 h-full flex flex-col bg-surface border-l border-accent">
      <div className="px-4 pt-14 pb-3 border-b border-accent">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-primary" />
          <h2 className="font-heading font-semibold text-sm text-foreground">Drivers & Routes</h2>
        </div>
        <p className="mt-1.5 text-[11px] text-muted">
          Click a driver for their route and manual stop controls.
        </p>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {onDutyFirst.map((d) => (
          <DriverRow
            key={d.id}
            driver={d}
            routeIndex={d.currentRoute ? routeIndexById[d.currentRoute.id] ?? 0 : 0}
            canReceive={!!selectedOrderId}
            onAssign={(orderId, driverId) => onAssign(orderId || selectedOrderId, driverId)}
            onOpen={onOpenDriver}
          />
        ))}
      </div>
    </aside>
  );
};

export default DriversPanel;
