from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Band:
    low: float
    high: float
    setpoint: float
    freeze_critical: float | None = None  # alum vaccines ≤0°C


@dataclass
class AssetSpec:
    asset_id: str
    label: str
    asset_class: str
    location: str
    floor: int
    zone: str
    map_x: float
    map_y: float
    band: Band | None
    tau_real_min: float = 12.0
    capacity_l: float = 40.0
    demo_role: str | None = None  # v3, v7, v4, v8, lwt
    thermal: bool = True


@dataclass
class UnitSpec:
    unit_id: str
    asset_id: str
    product_name: str
    lot: str
    expiry: str
    volume_l: float
    temp_band: str
    blood_type: str | None = None


@dataclass
class StaffSpec:
    id: str
    name: str
    cert: str
    floor: int


BLOOD = Band(2.0, 6.0, 4.0)
VAX = Band(2.0, 8.0, 5.0, freeze_critical=0.0)
INSULIN = Band(2.0, 8.0, 5.0, freeze_critical=0.0)
PLT = Band(20.0, 24.0, 22.0)
FFP = Band(-40.0, -30.0, -35.0)
WALKIN = Band(2.0, 8.0, 5.0, freeze_critical=0.0)

ASSETS: list[AssetSpec] = [
    AssetSpec("FREEZER_BLOOD_01", "RBC Vault 1", "blood_rbc", "Floor 1 — Blood Bank A", 1, "blood-a", 18, 28, BLOOD, capacity_l=48),
    AssetSpec("FREEZER_BLOOD_02", "RBC Vault 2", "blood_rbc", "Floor 1 — Blood Bank A", 1, "blood-a", 32, 28, BLOOD, capacity_l=48),
    AssetSpec("FREEZER_BLOOD_03", "RBC Vault 3 · backup", "blood_rbc", "Floor 1 — Blood Bank B", 1, "blood-b", 68, 30, BLOOD, capacity_l=56, demo_role="v7"),
    AssetSpec("FREEZER_BLOOD_04", "RBC Vault 4 · primary", "blood_rbc", "Floor 1 — Blood Bank B", 1, "blood-b", 82, 30, BLOOD, capacity_l=40, demo_role="v3"),
    AssetSpec("FREEZER_BLOOD_05", "ICU satellite 1", "blood_rbc", "Floor 2 — ICU Cold", 2, "icu", 22, 62, BLOOD, capacity_l=24, demo_role="v4"),
    AssetSpec("FREEZER_BLOOD_06", "ICU satellite 2", "blood_rbc", "Floor 2 — ICU Cold", 2, "icu", 36, 62, BLOOD, capacity_l=24),
    AssetSpec("ILR_VAX_01", "ILR Vaccines 1", "vaccine_ilr", "Floor 2 — Pharmacy", 2, "pharm", 70, 58, VAX, capacity_l=30),
    AssetSpec("ILR_VAX_02", "ILR Vaccines 2 · probe", "vaccine_ilr", "Floor 2 — Pharmacy", 2, "pharm", 84, 58, VAX, capacity_l=30, demo_role="lwt"),
    AssetSpec("ILR_VAX_03", "ILR Vaccines 3", "vaccine_ilr", "Floor 2 — Pharmacy", 2, "pharm", 70, 72, VAX, capacity_l=30),
    AssetSpec("ILR_VAX_04", "ILR Vaccines 4", "vaccine_ilr", "Floor 3 — OT prep", 3, "ot", 20, 82, VAX, capacity_l=20),
    AssetSpec("ILR_VAX_05", "ILR Vaccines 5", "vaccine_ilr", "Floor 3 — OT prep", 3, "ot", 34, 82, VAX, capacity_l=20),
    AssetSpec("ILR_INSULIN_01", "Insulin vault 1", "insulin_ilr", "Floor 2 — Pharmacy", 2, "pharm", 56, 58, INSULIN, capacity_l=18),
    AssetSpec("ILR_INSULIN_02", "Insulin vault 2", "insulin_ilr", "Floor 2 — Pharmacy", 2, "pharm", 56, 72, INSULIN, capacity_l=18),
    AssetSpec("ILR_INSULIN_03", "Insulin vault 3", "insulin_ilr", "Floor 1 — Ward store", 1, "ward", 18, 55, INSULIN, capacity_l=12),
    AssetSpec("PLT_AGIT_01", "Platelet agitator 1", "platelet", "Floor 1 — Blood Bank A", 1, "blood-a", 18, 42, PLT, tau_real_min=8.0, capacity_l=8),
    AssetSpec("PLT_AGIT_02", "Platelet agitator 2", "platelet", "Floor 1 — Blood Bank A", 1, "blood-a", 32, 42, PLT, tau_real_min=8.0, capacity_l=8),
    AssetSpec("PLASMA_FFP_01", "Plasma freezer 1", "plasma_ffp", "Floor 1 — Blood Bank B", 1, "blood-b", 68, 48, FFP, tau_real_min=8.0, capacity_l=36),
    AssetSpec("PLASMA_FFP_02", "Plasma freezer 2", "plasma_ffp", "Floor 3 — OT backup", 3, "ot", 80, 82, FFP, tau_real_min=8.0, capacity_l=36),
    AssetSpec("WALKIN_COLD_01", "Walk-in cold 1", "walkin_cold", "Floor 1 — Central cold", 1, "central", 50, 28, WALKIN, tau_real_min=18.0, capacity_l=120),
    AssetSpec("WALKIN_COLD_02", "Walk-in cold 2 · cascade", "walkin_cold", "Floor 3 — Central overflow", 3, "overflow", 50, 88, WALKIN, tau_real_min=18.0, capacity_l=120, demo_role="v8"),
    AssetSpec("CART_CRASH_01", "Crash cart A", "crash_cart", "Floor 3 — OT corridor", 3, "ot", 12, 90, None, thermal=False),
    AssetSpec("CART_CRASH_02", "Crash cart B", "crash_cart", "Floor 2 — ICU bay", 2, "icu", 12, 68, None, thermal=False),
    AssetSpec("CART_CRASH_03", "Crash cart C", "crash_cart", "Floor 1 — ER", 1, "er", 88, 55, None, thermal=False),
    AssetSpec("CART_CRASH_04", "Crash cart D", "crash_cart", "Floor 2 — Ward 2B", 2, "ward", 88, 72, None, thermal=False),
]

STAFF: list[StaffSpec] = [
    StaffSpec("nurse-rao", "Nurse Rao", "blood", 1),
    StaffSpec("tech-mehta", "Tech Mehta", "vaccine", 2),
    StaffSpec("engr-iyer", "Engr Iyer", "maintenance", 1),
]

INVENTORY: list[UnitSpec] = [
    UnitSpec("BAG-ONEG-01", "FREEZER_BLOOD_04", "Packed RBC", "B24-4411", "2026-09-04", 0.35, "2-6", "O-neg"),
    UnitSpec("BAG-ONEG-02", "FREEZER_BLOOD_04", "Packed RBC", "B24-4412", "2026-09-05", 0.35, "2-6", "O-neg"),
    UnitSpec("BAG-APOS-01", "FREEZER_BLOOD_04", "Packed RBC", "B24-4501", "2026-09-08", 0.35, "2-6", "A-pos"),
    UnitSpec("BAG-APOS-02", "FREEZER_BLOOD_04", "Packed RBC", "B24-4502", "2026-09-08", 0.35, "2-6", "A-pos"),
    UnitSpec("BAG-BPOS-01", "FREEZER_BLOOD_05", "Packed RBC", "B24-4601", "2026-09-03", 0.35, "2-6", "B-pos"),
    UnitSpec("BAG-OPOS-01", "FREEZER_BLOOD_05", "Packed RBC", "B24-4701", "2026-09-06", 0.35, "2-6", "O-pos"),
    UnitSpec("BAG-ONEG-03", "FREEZER_BLOOD_01", "Packed RBC", "B24-4101", "2026-09-10", 0.35, "2-6", "O-neg"),
    UnitSpec("VAX-PENTA-01", "ILR_VAX_02", "Pentavalent", "UIP-8821", "2027-01-12", 0.4, "2-8"),
    UnitSpec("INS-HUM-01", "ILR_INSULIN_01", "Human insulin", "INS-1902", "2026-12-01", 0.25, "2-8"),
    UnitSpec("INS-HUM-02", "ILR_INSULIN_03", "Human insulin", "INS-1908", "2026-12-01", 0.25, "2-8"),
]

HOSPITAL = "ELCIA Medical Centre"
SITE_ID = "elcia-emc"


def spec_by_id(asset_id: str) -> AssetSpec:
    for a in ASSETS:
        if a.asset_id == asset_id:
            return a
    raise KeyError(asset_id)
