/**
 * Unassigned orders panel — the dispatch queue, sorted by urgency.
 * Cards are drag sources and click-selectable; assignment completes on a
 * driver row (drop or click) in the DriversPanel.
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../base/utils';
import { orderUrgency, URGENCY_CHIP } from './urgency';
import { Package, Plus, GripVertical, ArrowUpRight } from 'lucide-react';

function fmtTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

function OrderCard({ order, selected, assigning, onSelect, now }) {
  const navigate = useNavigate();
  const u = orderUrgency(order, now);
  return (
    <div
      draggable={!assigning}
      onDragStart={(e) => {
        e.dataTransfer.setData('text/lip-order-id', order.id);
        e.dataTransfer.effectAllowed = 'move';
        onSelect(order.id);
      }}
      onClick={() => onSelect(selected ? null : order.id)}
      className={cn(
        'group rounded-card border p-3 cursor-pointer transition-all select-none',
        selected
          ? 'border-primary/70 bg-primary/10 shadow-card'
          : 'border-accent bg-surface-raised hover:border-primary/40',
        assigning && 'opacity-60 pointer-events-none'
      )}
    >
      <div className="flex items-center gap-2">
        <GripVertical className="w-3.5 h-3.5 text-muted/50 shrink-0" />
        <span className="font-heading font-semibold text-sm text-foreground">{order.orderNumber}</span>
        <span className={cn('ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full', URGENCY_CHIP[u.tone])}>
          {assigning ? 'assigning…' : u.label}
        </span>
      </div>
      <div className="mt-1.5 text-xs text-muted truncate pl-5">{order.customer?.name}</div>
      <div className="mt-1 pl-5 space-y-0.5">
        <div className="text-[11px] text-muted truncate">
          <span className="text-primary/80 font-semibold">P</span> {order.pickup?.address}
        </div>
        <div className="text-[11px] text-muted truncate">
          <span className="text-info font-semibold">D</span> {order.delivery?.address}
        </div>
      </div>
      <div className="mt-1.5 pl-5 flex items-center gap-3 text-[10px] text-muted/80">
        <span>{order.parcelCount} parcel{order.parcelCount === 1 ? '' : 's'}</span>
        <span>window {fmtTime(order.delivery?.windowStart)}–{fmtTime(order.delivery?.windowEnd)}</span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/orders/${order.id}`);
          }}
          className="ml-auto opacity-0 group-hover:opacity-100 flex items-center gap-0.5 text-primary hover:underline"
        >
          detail <ArrowUpRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}

const UnassignedPanel = ({ orders, selectedOrderId, assigningOrderIds, onSelect, now }) => {
  const navigate = useNavigate();
  const sorted = [...orders].sort((a, b) => {
    const ua = orderUrgency(a, now);
    const ub = orderUrgency(b, now);
    return ua.rank - ub.rank || (ua.mins ?? 9e9) - (ub.mins ?? 9e9);
  });

  return (
    <aside className="w-[320px] shrink-0 h-full flex flex-col bg-surface border-r border-accent">
      <div className="px-4 pt-14 pb-3 border-b border-accent">
        <div className="flex items-center gap-2">
          <Package className="w-4 h-4 text-warn" />
          <h2 className="font-heading font-semibold text-sm text-foreground">Unassigned</h2>
          <span className="text-xs text-muted">({orders.length})</span>
          <button
            onClick={() => navigate('/orders/new')}
            className="ml-auto flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-primary text-background hover:bg-primary/85"
          >
            <Plus className="w-3.5 h-3.5" /> New Order
          </button>
        </div>
        <p className="mt-1.5 text-[11px] text-muted">
          Drag onto a driver — or click an order, then a driver.
        </p>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {sorted.length === 0 ? (
          <div className="text-center text-xs text-muted py-10">
            Queue is clear — every order is on a route.
          </div>
        ) : (
          sorted.map((o) => (
            <OrderCard
              key={o.id}
              order={o}
              now={now}
              selected={o.id === selectedOrderId}
              assigning={assigningOrderIds.has(o.id)}
              onSelect={onSelect}
            />
          ))
        )}
      </div>
    </aside>
  );
};

export default UnassignedPanel;
