/** Time-window urgency for the dispatch board. */

export function minutesToWindowEnd(order, now = Date.now()) {
  const end = order.delivery?.windowEnd;
  if (!end) return null;
  return Math.round((new Date(end).getTime() - now) / 60000);
}

/**
 * Returns {rank, tone, label} — rank sorts (lower = more urgent), tone picks
 * the chip styling, label is human text.
 */
export function orderUrgency(order, now = Date.now()) {
  const mins = minutesToWindowEnd(order, now);
  const stat = order.serviceLevel === 'STAT';
  const rush = order.serviceLevel === 'RUSH';

  if (mins != null && mins < 0) {
    return { rank: 0, tone: 'late', label: `${-mins}m late`, mins };
  }
  if (stat) {
    return { rank: 1, tone: 'stat', label: mins != null ? `STAT · ${mins}m` : 'STAT', mins };
  }
  if (mins != null && mins <= 45) {
    return { rank: 2, tone: 'critical', label: `due in ${mins}m`, mins };
  }
  if (rush) {
    return { rank: 3, tone: 'rush', label: mins != null ? `RUSH · ${mins}m` : 'RUSH', mins };
  }
  if (mins != null && mins <= 120) {
    return { rank: 4, tone: 'soon', label: `due in ${formatMins(mins)}`, mins };
  }
  return { rank: 5, tone: 'ok', label: mins != null ? `due in ${formatMins(mins)}` : 'no window', mins };
}

function formatMins(mins) {
  if (mins < 60) return `${mins}m`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
}

export const URGENCY_CHIP = {
  late: 'bg-danger/20 text-danger border border-danger/40',
  stat: 'bg-danger/15 text-danger border border-danger/40 animate-pulse',
  critical: 'bg-danger/15 text-danger border border-danger/30',
  rush: 'bg-warn/15 text-warn border border-warn/30',
  soon: 'bg-warn/10 text-warn border border-warn/20',
  ok: 'bg-foreground/5 text-muted border border-accent',
};

export const SERVICE_CHIP = {
  STAT: 'bg-danger/15 text-danger border border-danger/40',
  RUSH: 'bg-warn/15 text-warn border border-warn/30',
  ROUTINE: 'bg-foreground/5 text-muted border border-accent',
};
