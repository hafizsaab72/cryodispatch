import { Link } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, RefreshControl, ScrollView, Text, View } from "react-native";
import * as Haptics from "expo-haptics";
import { fetchState, type Mission } from "../lib/api";

export default function Inbox() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    try {
      const s = await fetchState();
      setMissions(s.missions);
      setErr(null);
      if (s.missions.some((m) => m.status === "proposed")) {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "error");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 2000);
    return () => clearInterval(id);
  }, []);

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: "#04151c" }}
      contentContainerStyle={{ padding: 16, gap: 12 }}
      refreshControl={<RefreshControl refreshing={busy} onRefresh={load} tintColor="#2ec4b6" />}
    >
      <Text style={{ color: "#2ec4b6", fontSize: 12, letterSpacing: 2 }}>STAFF · NURSE RAO</Text>
      {err ? <Text style={{ color: "#e23d28" }}>{err}. Set EXPO_PUBLIC_PLANT_URL to your LAN IP.</Text> : null}
      {missions.length === 0 ? (
        <Text style={{ color: "#7fa3ad", marginTop: 24 }}>No open MOVEs. Waiting on the plant.</Text>
      ) : null}
      {missions.map((m) => (
        <Link key={m.id} href={`/mission/${m.id}`} asChild>
          <Pressable
            style={{
              borderColor: m.status === "proposed" ? "#e07a3d" : "#1c4654",
              borderWidth: 1,
              borderRadius: 12,
              padding: 14,
              backgroundColor: "#0b2430",
            }}
          >
            <Text style={{ color: "#2ec4b6", fontFamily: "Menlo", fontSize: 11 }}>{m.status.toUpperCase()}</Text>
            <Text style={{ color: "#d7f3f2", fontSize: 16, marginTop: 4 }}>
              {m.from_asset} → {m.to_asset}
            </Text>
            <Text style={{ color: "#7fa3ad", marginTop: 4 }}>
              {m.units.map((u) => u.blood_type || u.unit_id).join(", ")} · {m.distance_m} m · {m.eta_min} min
            </Text>
          </Pressable>
        </Link>
      ))}
    </ScrollView>
  );
}
