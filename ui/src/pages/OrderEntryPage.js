/**
 * Order entry — a real order-entry screen for the demo world.
 * Every submission becomes an order.created event on the backbone; the
 * address book stands in for a geocoder (see world/austin.js).
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../components/base/utils';
import api from '../api/client';
import { DEPOT, ADDRESS_BOOK, AUSTIN_CENTER } from '../world/austin';
import { SERVICE_CHIP } from '../components/dispatch/urgency';
import { Building2, MapPin, Clock, Boxes, Minus, Plus, Radio, Loader2, Send } from 'lucide-react';

const SERVICE_WINDOW_MINUTES = { ROUTINE: 180, RUSH: 120, STAT: 90 };

const SERVICE_OPTIONS = [
  { id: 'ROUTINE', blurb: 'standard window' },
  { id: 'RUSH', blurb: 'priority handling' },
  { id: 'STAT', blurb: 'medical-critical — tightest window', danger: true },
];

const INPUT_CLASS =
  'w-full px-3 py-2 text-sm rounded-xl border border-accent bg-surface-raised text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60';

function toInputValue(date) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function roundUpToQuarterHour(date) {
  const d = new Date(date);
  d.setSeconds(0, 0);
  const rem = d.getMinutes() % 15;
  if (rem !== 0) d.setMinutes(d.getMinutes() + (15 - rem));
  return d;
}

function addMinutes(inputValue, mins) {
  const d = new Date(inputValue);
  d.setMinutes(d.getMinutes() + mins);
  return toInputValue(d);
}

const fmtWindowEdge = (inputValue) =>
  inputValue
    ? new Date(inputValue).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
    : '—';

function Section({ icon: Icon, title, children }) {
  return (
    <section className="bg-surface border border-accent rounded-card shadow-card p-5">
      <h2 className="font-heading text-sm font-semibold text-foreground flex items-center gap-2">
        <Icon className="w-4 h-4 text-primary" /> {title}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function Segmented({ options, value, onChange }) {
  return (
    <div className="inline-flex flex-wrap rounded-xl border border-accent bg-surface-raised p-0.5">
      {options.map((opt) => (
        <button
          key={opt.id}
          type="button"
          disabled={opt.disabled}
          onClick={() => onChange(opt.id)}
          className={cn(
            'px-3 py-1.5 text-xs font-semibold rounded-[10px] transition-colors',
            value === opt.id ? 'bg-primary/15 text-primary' : 'text-muted hover:text-foreground',
            opt.disabled && 'opacity-40 cursor-not-allowed hover:text-muted'
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function PointReadout({ point, placeholder }) {
  if (!point) {
    return <div className="mt-3 text-xs text-muted italic">{placeholder}</div>;
  }
  return (
    <div className="mt-3 flex items-start gap-2 rounded-xl border border-accent bg-surface-raised px-3 py-2">
      <MapPin className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
      <div className="min-w-0">
        <div className="text-xs text-foreground truncate" title={point.address}>{point.address}</div>
        <div className="font-mono text-[10px] text-muted mt-0.5">
          {Number(point.latitude).toFixed(4)}, {Number(point.longitude).toFixed(4)}
        </div>
      </div>
    </div>
  );
}

const OrderEntryPage = () => {
  const navigate = useNavigate();

  const [customers, setCustomers] = useState([]);
  const [loadError, setLoadError] = useState(null);

  const [customerId, setCustomerId] = useState('');
  const [pickupMode, setPickupMode] = useState('DEPOT'); // DEPOT | CUSTOMER | BOOK
  const [pickupBookIdx, setPickupBookIdx] = useState('0');
  const [deliveryMode, setDeliveryMode] = useState('BOOK'); // BOOK | CUSTOM
  const [deliveryBookIdx, setDeliveryBookIdx] = useState('');
  const [customAddress, setCustomAddress] = useState('');
  const [customLat, setCustomLat] = useState(String(AUSTIN_CENTER.latitude));
  const [customLng, setCustomLng] = useState(String(AUSTIN_CENTER.longitude));

  const [readyAt, setReadyAt] = useState(() => toInputValue(roundUpToQuarterHour(new Date())));
  const [deliverBy, setDeliverBy] = useState(() =>
    addMinutes(toInputValue(roundUpToQuarterHour(new Date())), SERVICE_WINDOW_MINUTES.ROUTINE)
  );
  const [deliverByTouched, setDeliverByTouched] = useState(false);

  const [parcelCount, setParcelCount] = useState(1);
  const [serviceLevel, setServiceLevel] = useState('ROUTINE');
  const [notes, setNotes] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  useEffect(() => {
    api
      .listCustomers()
      .then((res) => setCustomers(res.customers || []))
      .catch((e) => setLoadError(e.message));
  }, []);

  const selectedCustomer = useMemo(
    () => customers.find((c) => c.id === customerId) || null,
    [customers, customerId]
  );

  const pickupPoint = useMemo(() => {
    if (pickupMode === 'DEPOT') {
      return { address: DEPOT.address, latitude: DEPOT.latitude, longitude: DEPOT.longitude };
    }
    if (pickupMode === 'CUSTOMER') {
      if (!selectedCustomer) return null;
      return {
        address: selectedCustomer.address,
        latitude: selectedCustomer.latitude,
        longitude: selectedCustomer.longitude,
      };
    }
    const entry = ADDRESS_BOOK[Number(pickupBookIdx)];
    return entry ? { address: entry.address, latitude: entry.latitude, longitude: entry.longitude } : null;
  }, [pickupMode, selectedCustomer, pickupBookIdx]);

  const deliveryPoint = useMemo(() => {
    if (deliveryMode === 'BOOK') {
      const entry = deliveryBookIdx === '' ? null : ADDRESS_BOOK[Number(deliveryBookIdx)];
      return entry ? { address: entry.address, latitude: entry.latitude, longitude: entry.longitude } : null;
    }
    const lat = Number(customLat);
    const lng = Number(customLng);
    if (!customAddress.trim() || !Number.isFinite(lat) || !Number.isFinite(lng)) return null;
    return { address: customAddress.trim(), latitude: lat, longitude: lng };
  }, [deliveryMode, deliveryBookIdx, customAddress, customLat, customLng]);

  const windowValid = useMemo(
    () => Boolean(readyAt && deliverBy && new Date(deliverBy).getTime() > new Date(readyAt).getTime()),
    [readyAt, deliverBy]
  );

  const changeReadyAt = useCallback(
    (value) => {
      setReadyAt(value);
      if (!deliverByTouched && value) {
        setDeliverBy(addMinutes(value, SERVICE_WINDOW_MINUTES[serviceLevel]));
      }
    },
    [deliverByTouched, serviceLevel]
  );

  const changeDeliverBy = useCallback((value) => {
    setDeliverBy(value);
    setDeliverByTouched(true);
  }, []);

  const changeServiceLevel = useCallback(
    (level) => {
      setServiceLevel(level);
      if (!deliverByTouched && readyAt) {
        setDeliverBy(addMinutes(readyAt, SERVICE_WINDOW_MINUTES[level]));
      }
    },
    [deliverByTouched, readyAt]
  );

  const canSubmit = Boolean(customerId && pickupPoint && deliveryPoint && windowValid) && !submitting;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const windowStart = new Date(readyAt).toISOString();
      const windowEnd = new Date(deliverBy).toISOString();
      const order = await api.createOrder({
        customerId,
        pickup: { ...pickupPoint, windowStart, windowEnd },
        delivery: { ...deliveryPoint, windowStart, windowEnd },
        parcelCount,
        serviceLevel,
        notes: notes.trim() || undefined,
      });
      navigate(`/orders/${order.id}`);
    } catch (err) {
      setSubmitError(err.message);
      setSubmitting(false);
    }
  };

  const label = (text) => (
    <label className="block text-[11px] font-semibold uppercase tracking-wide text-muted mb-1">{text}</label>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold text-foreground">New Order</h1>
        <p className="text-muted mt-1">Every submission becomes an order.created event on the backbone</p>
      </div>

      {loadError && (
        <div className="px-3 py-2 text-xs rounded-lg bg-danger/10 text-danger border border-danger/30">
          {loadError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="lg:col-span-2 space-y-4">
          <Section icon={Building2} title="Customer">
            {label('Bill-to customer')}
            <select
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              required
              className={INPUT_CLASS}
            >
              <option value="" disabled>
                Select customer…
              </option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.code})
                </option>
              ))}
            </select>
          </Section>

          <Section icon={MapPin} title="Pickup">
            <Segmented
              value={pickupMode}
              onChange={setPickupMode}
              options={[
                { id: 'DEPOT', label: 'Depot' },
                { id: 'CUSTOMER', label: 'Customer address', disabled: !selectedCustomer },
                { id: 'BOOK', label: 'Address book' },
              ]}
            />
            {pickupMode === 'BOOK' && (
              <div className="mt-3">
                {label('Pickup address')}
                <select
                  value={pickupBookIdx}
                  onChange={(e) => setPickupBookIdx(e.target.value)}
                  className={INPUT_CLASS}
                >
                  {ADDRESS_BOOK.map((entry, i) => (
                    <option key={entry.address} value={String(i)}>
                      {entry.address}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <PointReadout
              point={pickupPoint}
              placeholder="Select a customer to use their address as the pickup point."
            />
          </Section>

          <Section icon={MapPin} title="Delivery">
            <Segmented
              value={deliveryMode}
              onChange={setDeliveryMode}
              options={[
                { id: 'BOOK', label: 'Address book' },
                { id: 'CUSTOM', label: 'Custom' },
              ]}
            />
            {deliveryMode === 'BOOK' ? (
              <div className="mt-3">
                {label('Delivery address')}
                <select
                  value={deliveryBookIdx}
                  onChange={(e) => setDeliveryBookIdx(e.target.value)}
                  className={INPUT_CLASS}
                >
                  <option value="" disabled>
                    Select delivery address…
                  </option>
                  {ADDRESS_BOOK.map((entry, i) => (
                    <option key={entry.address} value={String(i)}>
                      {entry.address}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="mt-3 space-y-2">
                <div>
                  {label('Street address')}
                  <input
                    value={customAddress}
                    onChange={(e) => setCustomAddress(e.target.value)}
                    placeholder="e.g. 1100 Congress Ave, Austin, TX 78701"
                    className={INPUT_CLASS}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    {label('Latitude')}
                    <input
                      type="number"
                      step="0.0001"
                      value={customLat}
                      onChange={(e) => setCustomLat(e.target.value)}
                      className={INPUT_CLASS}
                    />
                  </div>
                  <div>
                    {label('Longitude')}
                    <input
                      type="number"
                      step="0.0001"
                      value={customLng}
                      onChange={(e) => setCustomLng(e.target.value)}
                      className={INPUT_CLASS}
                    />
                  </div>
                </div>
              </div>
            )}
            <PointReadout point={deliveryPoint} placeholder="Pick an address — this is the demo world's geocoder." />
          </Section>

          <Section icon={Clock} title="Timing">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                {label('Ready at')}
                <input
                  type="datetime-local"
                  value={readyAt}
                  onChange={(e) => changeReadyAt(e.target.value)}
                  className={INPUT_CLASS}
                  style={{ colorScheme: 'dark' }}
                />
              </div>
              <div>
                {label('Deliver by')}
                <input
                  type="datetime-local"
                  value={deliverBy}
                  onChange={(e) => changeDeliverBy(e.target.value)}
                  className={INPUT_CLASS}
                  style={{ colorScheme: 'dark' }}
                />
              </div>
            </div>
            {!windowValid && readyAt && deliverBy ? (
              <p className="mt-2 text-[11px] text-danger">Deliver-by must be after ready-at.</p>
            ) : (
              <p className="mt-2 text-[11px] text-muted">
                Deliver-by follows the service level ({SERVICE_WINDOW_MINUTES[serviceLevel]} min) until you edit it
                yourself.
              </p>
            )}
          </Section>

          <Section icon={Boxes} title="Parcels & service">
            <div className="flex flex-wrap items-end gap-6">
              <div>
                {label('Parcels (1–20)')}
                <div className="inline-flex items-center rounded-xl border border-accent bg-surface-raised">
                  <button
                    type="button"
                    onClick={() => setParcelCount((n) => Math.max(1, n - 1))}
                    disabled={parcelCount <= 1}
                    className="p-2 text-muted hover:text-foreground disabled:opacity-30"
                    aria-label="Fewer parcels"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                  <span className="w-10 text-center text-sm font-semibold text-foreground tabular-nums">
                    {parcelCount}
                  </span>
                  <button
                    type="button"
                    onClick={() => setParcelCount((n) => Math.min(20, n + 1))}
                    disabled={parcelCount >= 20}
                    className="p-2 text-muted hover:text-foreground disabled:opacity-30"
                    aria-label="More parcels"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-4">
              {label('Service level')}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {SERVICE_OPTIONS.map((opt) => {
                  const selected = serviceLevel === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => changeServiceLevel(opt.id)}
                      className={cn(
                        'rounded-xl border p-3 text-left transition-colors',
                        selected
                          ? opt.danger
                            ? 'border-danger/60 bg-danger/10'
                            : 'border-primary/70 bg-primary/10'
                          : cn(
                              'border-accent bg-surface-raised',
                              opt.danger ? 'hover:border-danger/40' : 'hover:border-primary/40'
                            )
                      )}
                    >
                      <div
                        className={cn(
                          'text-xs font-bold tracking-wide',
                          selected ? (opt.danger ? 'text-danger' : 'text-primary') : 'text-foreground'
                        )}
                      >
                        {opt.id}
                      </div>
                      <div className={cn('mt-0.5 text-[11px]', opt.danger ? 'text-danger/80' : 'text-muted')}>
                        {opt.blurb}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="mt-4">
              {label('Notes (optional)')}
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="Gate codes, handling instructions…"
                className={cn(INPUT_CLASS, 'resize-y')}
              />
            </div>
          </Section>
        </div>

        <aside className="lg:sticky lg:top-6 bg-surface border border-accent rounded-card shadow-card p-5 space-y-4">
          <h2 className="font-heading text-sm font-semibold text-foreground">Order summary</h2>

          <dl className="space-y-3">
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted">Customer</dt>
              <dd className="mt-0.5 text-xs text-foreground">
                {selectedCustomer ? `${selectedCustomer.name} (${selectedCustomer.code})` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted">Pickup → Delivery</dt>
              <dd className="mt-0.5 space-y-0.5">
                <div className="text-xs text-foreground truncate" title={pickupPoint?.address}>
                  <span className="text-primary/80 font-semibold">P</span> {pickupPoint?.address || '—'}
                </div>
                <div className="text-xs text-foreground truncate" title={deliveryPoint?.address}>
                  <span className="text-info font-semibold">D</span> {deliveryPoint?.address || '—'}
                </div>
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted">Window</dt>
              <dd className="mt-0.5 text-xs text-foreground">
                {fmtWindowEdge(readyAt)} → {fmtWindowEdge(deliverBy)}
              </dd>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-foreground">
                {parcelCount} parcel{parcelCount === 1 ? '' : 's'}
              </span>
              <span
                className={cn(
                  'text-[10px] font-semibold px-2 py-0.5 rounded-full',
                  SERVICE_CHIP[serviceLevel] || SERVICE_CHIP.ROUTINE
                )}
              >
                {serviceLevel}
              </span>
            </div>
          </dl>

          {submitError && (
            <div className="px-3 py-2 text-xs rounded-lg bg-danger/10 text-danger border border-danger/30">
              {submitError}
            </div>
          )}

          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-xl bg-primary text-background hover:bg-primary/85 disabled:opacity-40"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Creating order…
              </>
            ) : (
              <>
                <Send className="w-4 h-4" /> Create order
              </>
            )}
          </button>

          <p className="text-[11px] text-muted leading-relaxed flex items-start gap-1.5">
            <Radio className="w-3.5 h-3.5 text-primary shrink-0 mt-px" />
            <span>
              Submitting emits <span className="font-mono text-primary">order.created</span> — watch it land on the
              Dispatch Board and Event Console.
            </span>
          </p>
        </aside>
      </form>
    </div>
  );
};

export default OrderEntryPage;
