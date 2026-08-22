-- CryoDispatch plant schema for project cefhoczywrycsbniywus (ap-south-1).
-- Empty project — one clean migration. Do not reuse Lensora.
-- Anon: SELECT only. Writes go through the service role (plant + intent function).
-- Column names are snake_case; plant/shared camel fields map at the boundary
-- (dT_dt_c_per_min -> dt_dt_c_per_min, predicted_T_60s_c -> predicted_t_60s_c).

create table public.plant_meta (
  site_id text primary key,
  hospital text not null,
  tick bigint not null default 0,
  updated_at timestamptz not null default now()
);

create table public.asset_state (
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
  timestamp double precision,
  minutes_to_breach double precision,
  risk_score double precision,
  remaining_efficacy_pct double precision,
  t_eq_c double precision,
  tau_min double precision,
  mkt_c double precision,
  dt_dt_c_per_min double precision,
  predicted_t_60s_c double precision,
  breach_threshold_c double precision,
  breach_direction text,
  model_mode text,
  confidence double precision,
  fault_class text,
  band_low_c double precision,
  band_high_c double precision,
  setpoint_c double precision,
  capacity_l double precision,
  used_l double precision,
  reserved_l double precision,
  free_l double precision,
  baseline_used_l double precision,
  sensor_id text,
  demo_role text,
  recent_c jsonb not null default '[]',
  updated_at timestamptz default now()
);

create table public.telemetry (
  id bigint generated always as identity primary key,
  asset_id text not null references public.asset_state (asset_id) on delete cascade,
  payload jsonb not null,
  created_at timestamptz default now()
);

create index telemetry_asset_created_idx on public.telemetry (asset_id, created_at desc);

create table public.alerts (
  id text primary key,
  asset_id text not null,
  kind text not null,
  severity text not null,
  message text not null,
  acked_at timestamptz,
  created_at timestamptz default now()
);

create table public.tickets (
  id text primary key,
  alert_id text,
  asset_id text not null,
  kind text not null,
  duty_cycle double precision,
  twin_duty_cycle double precision,
  parts text,
  sla_min double precision,
  kwh_hold_30m double precision,
  kwh_move double precision,
  created_at timestamptz default now()
);

create table public.missions (
  id text primary key,
  alert_id text,
  from_asset text not null,
  from_label text,
  to_asset text not null,
  to_label text,
  units jsonb not null default '[]',
  staff_id text,
  staff_name text,
  status text not null default 'proposed',
  eta_min double precision,
  distance_m double precision,
  ticket jsonb,
  scan_step text default 'unit',
  last_reject text,
  routing jsonb,
  events jsonb not null default '[]',
  created_at timestamptz default now()
);

create table public.audit_events (
  id text primary key,
  actor text not null,
  action text not null,
  old_value text,
  new_value text,
  reason text,
  payload_hash text,
  created_at timestamptz default now()
);

create table public.inventory (
  unit_id text primary key,
  asset_id text not null,
  home_asset_id text,
  product_name text not null,
  blood_type text,
  lot text,
  expiry date,
  volume_l double precision,
  temp_band text
);

create table public.staff (
  id text primary key,
  name text not null,
  cert text not null,
  floor int not null,
  busy boolean default false
);

create table public.custody_documents (
  mission_id text primary key,
  doc jsonb not null,
  updated_at timestamptz default now()
);

create table public.plant_intents (
  id uuid primary key default gen_random_uuid(),
  kind text not null,
  payload jsonb not null default '{}',
  status text not null default 'pending',
  result jsonb,
  error text,
  created_at timestamptz default now(),
  processed_at timestamptz
);

create index plant_intents_pending_idx on public.plant_intents (created_at)
  where status = 'pending';

alter table public.asset_state replica identity full;
alter table public.alerts replica identity full;
alter table public.missions replica identity full;
alter table public.tickets replica identity full;
alter table public.inventory replica identity full;
alter table public.staff replica identity full;
alter table public.plant_meta replica identity full;
alter table public.custody_documents replica identity full;
alter table public.audit_events replica identity full;

alter publication supabase_realtime add table public.asset_state;
alter publication supabase_realtime add table public.alerts;
alter publication supabase_realtime add table public.missions;
alter publication supabase_realtime add table public.tickets;
alter publication supabase_realtime add table public.inventory;
alter publication supabase_realtime add table public.staff;
alter publication supabase_realtime add table public.plant_meta;
alter publication supabase_realtime add table public.custody_documents;

alter table public.asset_state enable row level security;
alter table public.telemetry enable row level security;
alter table public.alerts enable row level security;
alter table public.tickets enable row level security;
alter table public.missions enable row level security;
alter table public.audit_events enable row level security;
alter table public.inventory enable row level security;
alter table public.staff enable row level security;
alter table public.custody_documents enable row level security;
alter table public.plant_meta enable row level security;
alter table public.plant_intents enable row level security;

-- Anon may read the live plant. Writes are service-role only (RLS bypass).
create policy "anon read asset_state" on public.asset_state for select to anon, authenticated using (true);
create policy "anon read telemetry" on public.telemetry for select to anon, authenticated using (true);
create policy "anon read alerts" on public.alerts for select to anon, authenticated using (true);
create policy "anon read tickets" on public.tickets for select to anon, authenticated using (true);
create policy "anon read missions" on public.missions for select to anon, authenticated using (true);
create policy "anon read audit" on public.audit_events for select to anon, authenticated using (true);
create policy "anon read inventory" on public.inventory for select to anon, authenticated using (true);
create policy "anon read staff" on public.staff for select to anon, authenticated using (true);
create policy "anon read custody" on public.custody_documents for select to anon, authenticated using (true);
create policy "anon read plant_meta" on public.plant_meta for select to anon, authenticated using (true);

grant usage on schema public to anon, authenticated;
grant select on
  public.asset_state,
  public.telemetry,
  public.alerts,
  public.tickets,
  public.missions,
  public.audit_events,
  public.inventory,
  public.staff,
  public.custody_documents,
  public.plant_meta
to anon, authenticated;
