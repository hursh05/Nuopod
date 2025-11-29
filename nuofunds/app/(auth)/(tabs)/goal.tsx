import { PageView } from "@/components/Themed";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import React from "react";
import { Text } from "react-native";

export default function CreateGoalScreen() {
  
  return (
    <PageView className="flex-1 justify-center items-center px-4">
      <MaterialCommunityIcons
        name="rocket-launch-outline"
        size={60}
        color="#888"
        style={{ marginBottom: 20 }}
      />

      <Text className="text-white text-2xl font-semibold mb-2">
        Goals
      </Text>

      <Text className="text-gray-400 text-base text-center px-6">
        This feature is coming soon 🚀  
      </Text>
    </PageView>

  );
}
