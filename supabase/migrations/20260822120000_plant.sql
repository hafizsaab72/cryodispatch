-- CryoDispatch plant schema (new project — do not reuse Lensora)

create table if not exists public.asset_state (
  asset_id text primary key,
  asset_class text not null,
  label text,
  location text,
  floor int,
  zone text,
  temperature double precision,
  door_status text,
  compressor_health double precision,
  battery_pct double precision,
  probe_online boolean default true,
  map_x double precision,
  map_y double precision,
  topic text,
  minutes_to_breach double precision,
  risk_score double precision,
  remaining_efficacy_pct double precision,
  t_eq_c double precision,
  tau_min double precision,
  mkt_c double precision,
  dt_dt_c_per_min double precision,
  predicted_t_60s_c double precision,
  breach_threshold_c double precision,
  model_mode text,
  confidence double precision,
  fault_class text,
  band_low_c double precision,
  band_high_c double precision,
  updated_at timestamptz default now()
);

create table if not exists public.telemetry (
  id bigint generated always as identity primary key,
  asset_id text not null references public.asset_state (asset_id) on delete cascade,
  payload jsonb not null,
  created_at timestamptz default now()
);

create index if not exists telemetry_asset_created_idx on public.telemetry (asset_id, created_at desc);

create table if not exists public.alerts (
  id text primary key,
  asset_id text not null,
  kind text not null,
  severity text not null,
  message text not null,
  acked_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists public.missions (
  id text primary key,
  alert_id text,
  from_asset text not null,
  to_asset text not null,
  units jsonb not null default '[]',
  staff_id text,
  staff_name text,
  status text not null default 'proposed',
  eta_min double precision,
  distance_m double precision,
  ticket jsonb,
  scan_step text default 'unit',
  last_reject text,
  created_at timestamptz default now()
);

create table if not exists public.audit_events (
  id text primary key,
  actor text not null,
  action text not null,
  old_value text,
  new_value text,
  reason text,
  payload_hash text,
  created_at timestamptz default now()
);

create table if not exists public.inventory (
  unit_id text primary key,
  asset_id text not null,
  product_name text not null,
  blood_type text,
  lot text,
  expiry date,
  volume_l double precision,
  temp_band text
);

create table if not exists public.staff (
  id text primary key,
  name text not null,
  cert text not null,
  floor int not null,
  busy boolean default false
);

alter table public.asset_state replica identity full;
alter table public.alerts replica identity full;
alter table public.missions replica identity full;
alter table public.audit_events replica identity full;

alter publication supabase_realtime add table public.asset_state;
alter publication supabase_realtime add table public.alerts;
alter publication supabase_realtime add table public.missions;

-- Demo-open RLS: one plant, one authenticated role. Tighten before any real hospital.
alter table public.asset_state enable row level security;
alter table public.telemetry enable row level security;
alter table public.alerts enable row level security;
alter table public.missions enable row level security;
alter table public.audit_events enable row level security;
alter table public.inventory enable row level security;
alter table public.staff enable row level security;

create policy "demo read asset_state" on public.asset_state for select using (true);
create policy "demo write asset_state" on public.asset_state for all using (true) with check (true);
create policy "demo read telemetry" on public.telemetry for select using (true);
create policy "demo write telemetry" on public.telemetry for insert with check (true);
create policy "demo read alerts" on public.alerts for select using (true);
create policy "demo write alerts" on public.alerts for all using (true) with check (true);
create policy "demo read missions" on public.missions for select using (true);
create policy "demo write missions" on public.missions for all using (true) with check (true);
create policy "demo read audit" on public.audit_events for select using (true);
create policy "demo write audit" on public.audit_events for insert with check (true);
create policy "demo read inventory" on public.inventory for select using (true);
create policy "demo write inventory" on public.inventory for all using (true) with check (true);
create policy "demo read staff" on public.staff for select using (true);
create policy "demo write staff" on public.staff for all using (true) with check (true);
