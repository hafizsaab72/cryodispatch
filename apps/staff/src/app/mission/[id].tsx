import { useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import * as Haptics from "expo-haptics";
import { acceptMission, fetchMission, type Mission } from "../../lib/api";

export default function MissionScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [m, setM] = useState<Mission | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    if (!id) {
      setLoading(false);
      setError("Mission not found");
      return;
    }
    setLoading(true);
    fetchMission(id)
      .then((found) => {
        setM(found);
        setError(found ? null : "Mission not found");
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(load, [load]);

  const onAccept = useCallback(async () => {
    if (!m || busy) return;
    setBusy(true);
    try {
      const next = await acceptMission(m.id);
      setM(next);
      setError(null);
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      router.push({ pathname: "/scan", params: { id: m.id } });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Accept failed");
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setBusy(false);
    }
  }, [m, busy, router]);

  if (loading && !m) {
    return <Text style={{ color: "#7fa3ad", padding: 24, fontSize: 15 }}>Loading…</Text>;
  }
  if (error && !m) {
    return (
      <View style={{ padding: 24, gap: 12 }}>
        <Text style={{ color: "#ff6a5a", fontSize: 15 }}>{error}</Text>
        <Pressable onPress={() => router.replace("/")}>
          <Text style={{ color: "#2ec4b6", fontSize: 15 }}>Back to inbox</Text>
        </Pressable>
      </View>
    );
  }
  if (!m) {
    return <Text style={{ color: "#7fa3ad", padding: 24, fontSize: 15 }}>Loading…</Text>;
  }

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: "#04151c" }}
      contentContainerStyle={{ padding: 20, gap: 12 }}
    >
      <Text style={{ color: "#2ec4b6", letterSpacing: 2, fontSize: 13 }}>LOCKED PLAN</Text>
      <Text style={{ color: "#d7f3f2", fontSize: 24, fontWeight: "700" }}>
        {m.from_asset} → {m.to_asset}
      </Text>

      <View style={{ backgroundColor: "#0b2430", borderRadius: 10, padding: 14, gap: 6 }}>
        {m.units.map((u) => (
          <Text key={u.unit_id} style={{ color: "#d7f3f2", fontSize: 15 }}>
            {u.product_name} · {u.blood_type ?? u.unit_id}
          </Text>
        ))}
      </View>

      <Text style={{ color: "#d7f3f2", fontSize: 15 }}>
        {m.staff_name ?? "No certified courier free"} · {m.distance_m} m
      </Text>
      <Text style={{ color: "#7fa3ad", fontSize: 14 }}>
        Hold {m.ticket.kwh_hold_30m} kWh vs move {m.ticket.kwh_move} kWh
      </Text>
      <Text style={{ color: "#7fa3ad", fontSize: 14 }}>Ticket: {m.ticket.parts}</Text>

      {error ? <Text style={{ color: "#ff6a5a", fontSize: 14 }}>{error}</Text> : null}

      {m.status === "proposed" ? (
        <Pressable
          onPress={onAccept}
          disabled={busy}
          style={{
            backgroundColor: busy ? "#1c4654" : "#2ec4b6",
            borderRadius: 12,
            padding: 16,
            marginTop: 12,
          }}
        >
          <Text style={{ color: "#04151c", textAlign: "center", fontWeight: "700", fontSize: 16 }}>
            {busy ? "Accepting…" : "ACCEPT MOVE"}
          </Text>
        </Pressable>
      ) : (
        <Pressable
          onPress={() => router.push({ pathname: "/scan", params: { id: m.id } })}
          style={{
            borderColor: "#2ec4b6",
            borderWidth: 1,
            borderRadius: 12,
            padding: 16,
            marginTop: 12,
          }}
        >
          <Text style={{ color: "#2ec4b6", textAlign: "center", fontSize: 15 }}>
            Continue scan ({m.scan_step})
          </Text>
        </Pressable>
      )}
    </ScrollView>
  );
}
