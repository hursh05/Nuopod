// FloatingChatButton.tsx
import { Text, View } from "@/components/Themed";
import { usePathname, useRouter } from "expo-router";
import React from "react";
import { TouchableOpacity } from "react-native";

const arr = ['/home', '/profile'];
export function FloatingChatButton() {
  const router = useRouter();
  const currentPath = usePathname();
  console.log("currentPath >>", currentPath);

  return (
    <View className="absolute bottom-[120px] right-4 !bg-transparent" style={{ 
       display: arr.includes(currentPath) ? "flex" : "none",
     }}>
      <TouchableOpacity
        onPress={() => router.push("/(auth)/chatScreen")}
        activeOpacity={0.8}
        className="bg-[#0866FF] px-4 py-3 rounded-full flex-row items-center shadow-lg"
      >
        <Text className="text-white text-xs font-semibold mr-2">
          Chat with NuoBot
        </Text>
        <View className="w-6 h-6 rounded-full bg-emerald-700 items-center justify-center">
          <Text className="text-white text-xs">💬</Text>
        </View>
      </TouchableOpacity>
    </View>
  );
}
