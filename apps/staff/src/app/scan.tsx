import { CameraView, useCameraPermissions } from "expo-camera";
import { useLocalSearchParams } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { Pressable, ScrollView, Text, TextInput, View } from "react-native";
import * as Haptics from "expo-haptics";
import { fetchMission, scanMission, USING_CLOUD, type Mission } from "../lib/api";

const STEP_HINT: Record<string, string> = {
  unit: "Scan the bag QR",
  source: "Scan the SOURCE vault",
  dest: "Scan the DESTINATION vault",
  done: "Custody closed",
};

export default function ScanScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [permission, requestPermission] = useCameraPermissions();
  const [m, setM] = useState<Mission | null>(null);
  const [typed, setTyped] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const lastCode = useRef<string | null>(null);
  const inflight = useRef(false);

  useEffect(() => {
    if (!id) return;
    fetchMission(id)
      .then(setM)
      .catch((e: Error) => setError(e.message));
  }, [id]);

  const apply = useCallback(
    async (raw: string) => {
      const code = raw.trim().toUpperCase();
      if (!id || inflight.current || !code) return;
      // Ignore the same sticker sitting in frame; only a new code is a new scan.
      if (code === lastCode.current) return;
      lastCode.current = code;
      inflight.current = true;
      setBusy(true);
      try {
        const next = await scanMission(id, code);
        setM(next);
        setError(null);
        await Haptics.notificationAsync(
          next.last_reject
            ? Haptics.NotificationFeedbackType.Error
            : Haptics.NotificationFeedbackType.Success,
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : "Scan failed");
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      } finally {
        inflight.current = false;
        setBusy(false);
        setTyped("");
        // Allow the same sticker to be re-scanned after a short pause.
        setTimeout(() => {
          lastCode.current = null;
        }, 1500);
      }
    },
    [id],
  );

  const step = m?.scan_step ?? "unit";
  const done = m?.status === "complete";

  return (
    <ScrollView style={{ flex: 1, backgroundColor: "#04151c" }}>
      {permission?.granted ? (
        <CameraView
          style={{ height: 260 }}
          barcodeScannerSettings={{ barcodeTypes: ["qr"] }}
          onBarcodeScanned={busy || done ? undefined : ({ data }) => apply(data)}
        />
      ) : (
        <Pressable
          onPress={requestPermission}
          style={{ height: 120, justifyContent: "center", backgroundColor: "#0b2430" }}
        >
          <Text style={{ color: "#2ec4b6", textAlign: "center", fontSize: 16 }}>
            Tap to enable camera, or type a code below
          </Text>
        </Pressable>
      )}

      <View style={{ padding: 16, gap: 12 }}>
        <Text style={{ color: "#2ec4b6", fontSize: 18, fontWeight: "700" }}>{STEP_HINT[step]}</Text>

        {m ? (
          <View style={{ backgroundColor: "#0b2430", borderRadius: 10, padding: 12, gap: 4 }}>
            <Text style={{ color: "#7fa3ad", fontSize: 13 }}>Source</Text>
            <Text style={{ color: "#d7f3f2", fontSize: 15 }}>{m.from_asset}</Text>
            <Text style={{ color: "#7fa3ad", fontSize: 13, marginTop: 6 }}>Destination</Text>
            <Text style={{ color: "#d7f3f2", fontSize: 15, fontWeight: "700" }}>{m.to_asset}</Text>
          </View>
        ) : null}

        {m?.last_reject ? (
          <View style={{ backgroundColor: "#3a1210", borderRadius: 10, padding: 14 }}>
            <Text style={{ color: "#ff6a5a", fontSize: 17, fontWeight: "700" }}>REJECTED</Text>
            <Text style={{ color: "#ffd9d4", fontSize: 15, marginTop: 4 }}>{m.last_reject}</Text>
          </View>
        ) : null}

        {error ? (
          <View style={{ backgroundColor: "#3a1210", borderRadius: 10, padding: 14 }}>
            <Text style={{ color: "#ff6a5a", fontSize: 15 }}>{error}</Text>
            <Text style={{ color: "#ffd9d4", fontSize: 13, marginTop: 6 }}>
              {USING_CLOUD
                ? "Start the plant so it can publish, or unset EXPO_PUBLIC_SUPABASE_* to use the LAN."
                : "Set EXPO_PUBLIC_PLANT_URL to the laptop's LAN IP and reload."}
            </Text>
          </View>
        ) : null}

        {done ? (
          <Text style={{ color: "#3ddc97", fontSize: 18, fontWeight: "700" }}>
            Custody closed. The command centre sees the check-in live.
          </Text>
        ) : null}

        <TextInput
          placeholder="UNIT:BAG-ONEG-01 or VAULT:FREEZER_BLOOD_04"
          placeholderTextColor="#5c7f8a"
          value={typed}
          onChangeText={setTyped}
          autoCapitalize="characters"
          autoCorrect={false}
          spellCheck={false}
          editable={!done}
          style={{
            borderColor: "#1c4654",
            borderWidth: 1,
            borderRadius: 8,
            padding: 12,
            color: "#d7f3f2",
            fontSize: 15,
          }}
        />
        <Pressable
          onPress={() => {
            lastCode.current = null;
            apply(typed);
          }}
          disabled={busy || done}
          style={{
            backgroundColor: busy || done ? "#1c4654" : "#2ec4b6",
            borderRadius: 10,
            padding: 14,
          }}
        >
          <Text style={{ color: "#04151c", textAlign: "center", fontWeight: "700", fontSize: 15 }}>
            {busy ? (USING_CLOUD ? "Waiting on plant…" : "Checking…") : "Submit code"}
          </Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}
