import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

export default function Layout() {
  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: "#04151c" },
          headerTintColor: "#d7f3f2",
          contentStyle: { backgroundColor: "#04151c" },
        }}
      >
        <Stack.Screen name="index" options={{ title: "CryoDispatch" }} />
        <Stack.Screen name="mission/[id]" options={{ title: "MOVE" }} />
        <Stack.Screen name="scan" options={{ title: "Scan custody" }} />
      </Stack>
    </>
  );
}
