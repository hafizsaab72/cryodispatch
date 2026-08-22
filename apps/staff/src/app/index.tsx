import { Link } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { Pressable, RefreshControl, ScrollView, Text, View } from "react-native";
import * as Haptics from "expo-haptics";
import { fetchState, PLANT_URL, USING_CLOUD, type Mission } from "../lib/api";

export default function Inbox() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const buzzed = useRef<Set<string>>(new Set());

  async function load(manual = false) {
    if (manual) setRefreshing(true);
    try {
      const s = await fetchState();
      setMissions(s.missions);
      setErr(null);
      // Buzz once per new MOVE, not on every poll.
      for (const m of s.missions) {
        if (m.status === "proposed" && !buzzed.current.has(m.id)) {
          buzzed.current.add(m.id);
          await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        }
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "error");
    } finally {
      if (manual) setRefreshing(false);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(() => load(), 2000);
    return () => clearInterval(id);
  }, []);

  const open = missions.filter((m) => m.status !== "cancelled");

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: "#04151c" }}
      contentContainerStyle={{ padding: 16, gap: 12 }}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor="#2ec4b6" />
      }
    >
      <Text style={{ color: "#2ec4b6", fontSize: 13, letterSpacing: 2 }}>STAFF · NURSE RAO</Text>
      <Text style={{ color: "#5c7f8a", fontSize: 12 }}>
        {USING_CLOUD ? "Supabase Realtime (plant must be publishing)" : PLANT_URL}
      </Text>

      {err ? (
        <View style={{ backgroundColor: "#3a1210", borderRadius: 10, padding: 14 }}>
          <Text style={{ color: "#ff6a5a", fontSize: 15 }}>{err}</Text>
          <Text style={{ color: "#ffd9d4", fontSize: 13, marginTop: 6 }}>
            {USING_CLOUD
              ? "Start the plant so it can publish, or unset EXPO_PUBLIC_SUPABASE_* to use the LAN."
              : "Set EXPO_PUBLIC_PLANT_URL to the laptop's LAN IP and reload."}
          </Text>
        </View>
      ) : null}

      {open.length === 0 && !err ? (
        <Text style={{ color: "#7fa3ad", marginTop: 24, fontSize: 15 }}>
          No open MOVEs. Waiting on the plant.
        </Text>
      ) : null}

      {open.map((m) => (
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
            <Text style={{ color: "#2ec4b6", fontSize: 12, letterSpacing: 1 }}>
              {m.status.toUpperCase()}
            </Text>
            <Text style={{ color: "#d7f3f2", fontSize: 17, marginTop: 4, fontWeight: "600" }}>
              {m.from_asset} → {m.to_asset}
            </Text>
            <Text style={{ color: "#7fa3ad", marginTop: 4, fontSize: 14 }}>
              {m.units.map((u) => u.blood_type || u.unit_id).join(", ")} · {m.distance_m} m ·{" "}
              {m.eta_min} min
            </Text>
          </Pressable>
        </Link>
      ))}
    </ScrollView>
  );
}
