// components/PasswordInput.tsx
import AntDesign from '@expo/vector-icons/AntDesign';
import React from "react";
import { Pressable, TextInput } from "react-native";
import { View } from "./Themed";

type Props = {
  label?: string;
  value: string;
  onChangeText: (t: string) => void;
  placeholder?: string;
  secure?: boolean; // ignored here, this component always supports toggle
  keyboardType?: any;
  show: boolean;
  onToggle: () => void;
};

export default function PasswordInput({
  label,
  value,
  onChangeText,
  placeholder,
  keyboardType,
  show,
  onToggle,
}: Props) {
  return (
    <View className="w-full mb-4">
      {/* {label ? <Text className="text-sm text-gray-600 mb-2">{label}</Text> : null} */}
      <View className="relative">
        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          secureTextEntry={!show}
          keyboardType={keyboardType}
          className="border-b border-gray-200 px-3 py-3 text-white pr-12"
          placeholderTextColor="#9CA3AF"
          accessibilityLabel={label ?? placeholder}
        />
        <Pressable
          onPress={onToggle}
          className="absolute right-2 top-1 px-2 py-1"
          accessibilityRole="button"
          accessibilityLabel={show ? "Hide password" : "Show password"}
        >
          {
            show ? <AntDesign name="eye-invisible" size={24} color="#9CA3AF" /> : <AntDesign name="eye" size={24} color="#9CA3AF" />
          }
        </Pressable>
      </View>
    </View>
  );
}
