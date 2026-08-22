import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, Text, View } from "react-native";
import * as Haptics from "expo-haptics";
import { acceptMission, fetchState, type Mission } from "../../lib/api";

export default function MissionScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [m, setM] = useState<Mission | null>(null);

  useEffect(() => {
    fetchState().then((s) => setM(s.missions.find((x) => x.id === id) ?? null));
  }, [id]);

  if (!m) {
    return <Text style={{ color: "#7fa3ad", padding: 24 }}>Loading…</Text>;
  }

  return (
    <View style={{ flex: 1, backgroundColor: "#04151c", padding: 20, gap: 12 }}>
      <Text style={{ color: "#2ec4b6", letterSpacing: 2, fontSize: 12 }}>LOCKED PLAN</Text>
      <Text style={{ color: "#d7f3f2", fontSize: 22, fontWeight: "600" }}>
        {m.from_asset} → {m.to_asset}
      </Text>
      <Text style={{ color: "#7fa3ad" }}>
        {m.units.map((u) => `${u.product_name} ${u.blood_type ?? u.unit_id}`).join("\n")}
      </Text>
      <Text style={{ color: "#d7f3f2" }}>
        {m.staff_name} · {m.distance_m} m · hold {m.ticket.kwh_hold_30m} kWh vs move {m.ticket.kwh_move} kWh
      </Text>
      <Text style={{ color: "#7fa3ad" }}>Ticket: {m.ticket.parts}</Text>
      {m.status === "proposed" ? (
        <Pressable
          onPress={async () => {
            const next = await acceptMission(m.id);
            setM(next);
            await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            router.push({ pathname: "/scan", params: { id: m.id } });
          }}
          style={{ backgroundColor: "#2ec4b6", borderRadius: 12, padding: 16, marginTop: 12 }}
        >
          <Text style={{ color: "#04151c", textAlign: "center", fontWeight: "700" }}>ACCEPT MOVE</Text>
        </Pressable>
      ) : (
        <Pressable
          onPress={() => router.push({ pathname: "/scan", params: { id: m.id } })}
          style={{ borderColor: "#2ec4b6", borderWidth: 1, borderRadius: 12, padding: 16, marginTop: 12 }}
        >
          <Text style={{ color: "#2ec4b6", textAlign: "center" }}>Continue scan ({m.scan_step})</Text>
        </Pressable>
      )}
    </View>
  );
}
