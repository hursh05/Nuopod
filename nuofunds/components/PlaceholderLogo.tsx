// components/PlaceholderLogo.tsx
import React from "react";
import { Text, View } from "./Themed";

export default function PlaceholderLogo({ size = 72 }: { size?: number }) {
  return (
    <View className="items-center">
      <View
        style={{ width: size, height: size, borderRadius: size / 8 }}
        className="items-center justify-center bg-gray-200"
      >
        <Text className="text-2xl font-bold text-gray-500">LOGO</Text>
      </View>
    </View>
  );
}
