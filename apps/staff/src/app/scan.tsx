import { CameraView, useCameraPermissions } from "expo-camera";
import { useLocalSearchParams } from "expo-router";
import { useRef, useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";
import * as Haptics from "expo-haptics";
import { scanMission, type Mission } from "../lib/api";

export default function ScanScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [permission, requestPermission] = useCameraPermissions();
  const [m, setM] = useState<Mission | null>(null);
  const [typed, setTyped] = useState("");
  const lock = useRef(false);

  async function apply(code: string) {
    if (!id || lock.current) return;
    lock.current = true;
    const next = await scanMission(id, code.trim());
    setM(next);
    if (next.last_reject) {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } else {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }
    setTimeout(() => {
      lock.current = false;
    }, 1200);
  }

  return (
    <View style={{ flex: 1, backgroundColor: "#04151c" }}>
      {permission?.granted ? (
        <CameraView
          style={{ height: 280 }}
          barcodeScannerSettings={{ barcodeTypes: ["qr"] }}
          onBarcodeScanned={({ data }) => apply(data)}
        />
      ) : (
        <Pressable onPress={requestPermission} style={{ height: 160, justifyContent: "center" }}>
          <Text style={{ color: "#2ec4b6", textAlign: "center" }}>Enable camera for QR</Text>
        </Pressable>
      )}
      <View style={{ padding: 16, gap: 10 }}>
        <Text style={{ color: "#7fa3ad" }}>
          Step: {m?.scan_step ?? "unit"} · unit → source vault → dest vault
        </Text>
        {m?.last_reject ? (
          <Text style={{ color: "#e23d28", fontSize: 16, fontWeight: "600" }}>{m.last_reject}</Text>
        ) : null}
        {m?.status === "complete" ? (
          <Text style={{ color: "#3ddc97", fontSize: 18 }}>Custody closed. Plant sees check-in live.</Text>
        ) : null}
        <TextInput
          placeholder="UNIT:BAG-ONEG-01 or VAULT:FREEZER_BLOOD_04"
          placeholderTextColor="#7fa3ad"
          value={typed}
          onChangeText={setTyped}
          autoCapitalize="characters"
          style={{
            borderColor: "#1c4654",
            borderWidth: 1,
            borderRadius: 8,
            padding: 12,
            color: "#d7f3f2",
          }}
        />
        <Pressable
          onPress={() => apply(typed)}
          style={{ backgroundColor: "#2ec4b6", borderRadius: 10, padding: 14 }}
        >
          <Text style={{ color: "#04151c", textAlign: "center", fontWeight: "700" }}>Submit code</Text>
        </Pressable>
      </View>
    </View>
  );
}
