// components/AuthInput.tsx
import React from "react";
import { TextInput, View } from "react-native";

type Props = {
  label?: string;
  value: string;
  onChangeText: (t: string) => void;
  placeholder?: string;
  secure?: boolean;
  keyboardType?: any;
};

export default function AuthInput({ label, value, onChangeText, placeholder, secure, keyboardType }: Props) {
  return (
    <View className="w-full mb-4">
      {/* {label ? <Text className="text-sm text-gray-600 mb-2">{label}</Text> : null} */}
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        secureTextEntry={secure}
        keyboardType={keyboardType}
        className="border-b border-gray-200 text-white px-3 py-3"
        placeholderTextColor="#9CA3AF"
        accessibilityLabel={label ?? placeholder}
      />
    </View>
  );
}