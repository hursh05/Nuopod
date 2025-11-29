// app/(auth)/profile.tsx
import { PageView, Text, View } from "@/components/Themed";
import { useAuthStore } from "@/store/useAuthStore";
import { useRouter } from "expo-router";
import React from "react";
import { Image, Pressable } from "react-native";

export default function ProfileScreen() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { consentGiven } = useAuthStore();

  const displayName = user?.name ?? user?.email ?? "Guest";
  const avatarSeed = encodeURIComponent(user?.name ?? user?.email ?? "guest");
  const avatarUrl = `https://avatar.iran.liara.run/username?username=${avatarSeed}`;

  return (
    <PageView className="flex-1 bg-gray-50 px-6 pt-8">
      {/* Profile card */}
      <View className="bg-white rounded-2xl p-5 shadow-sm">
        <View className="flex-row items-center">
          <Image
            source={{ uri: avatarUrl }}
            className="w-20 h-20 rounded-full bg-gray-200"
          />

          <View className="ml-4 flex-1">
            <Text className="text-lg font-semibold text-gray-900">
              {displayName}
            </Text>
            <Text className="text-sm text-gray-500 mt-1">
              {user?.email ?? ""}
            </Text>

            {/* Consent status moved here */}
            <View className="flex-row items-center justify-start gap-x-2 mt-2">
              <Text className="text-xs text-gray-500">Consent status:</Text>
              <Text
                className={`font-xs ${
                  consentGiven ? "!text-green-600" : "!text-red-500"
                }`}
              >
                {consentGiven ? "Approved" : "Grant Access"}
              </Text>
            </View>
          </View>
        </View>
      </View>

      {/* gap */}
      <View className="h-6" />

      {/* Actions */}
      <View className="bg-white rounded-2xl p-4 shadow-sm">
        {/* <Text className="text-sm font-medium text-gray-700 mb-3">Account</Text> */}

        {/* <Pressable
          onPress={() => console.log("Edit profile")}
          className="py-3 px-4 rounded-md bg-blue-600 items-center mb-3"
          android_ripple={{ color: "#2563eb" }}
        >
          <Text className="text-white font-semibold">Edit profile</Text>
        </Pressable> */}

        <Pressable
          onPress={() => router.push("/(auth)/consentScreen")}
          className="py-3 rounded-md  items-start mb-3"
          android_ripple={{ color: "#e5e7eb" }}
        >
          <Text className="text-gray-800 font-medium">Consent</Text>
        </Pressable>

        <Pressable
          onPress={() => router.push("/(auth)/manual-transaction")}
          className="py-3 rounded-md  items-start mb-3"
          android_ripple={{ color: "#e5e7eb" }}
        >
          <Text className="text-gray-800 font-medium">Manually Update Transaction</Text>
        </Pressable>

        <Pressable
          onPress={() => router.push("/(auth)/AdvisorConnect")}
          className="py-3 rounded-md  items-start mb-3"
          android_ripple={{ color: "#e5e7eb" }}
        >
          <Text className="text-gray-800 font-medium">Advisor Connect</Text>
        </Pressable>

        <Pressable
          onPress={() => router.push("/(auth)/EWA")}
          className="py-3 rounded-md items-start mb-3"
          android_ripple={{ color: "#e5e7eb" }}
        >
          <Text className="text-gray-800 font-medium">Earned Wage Access</Text>
        </Pressable>

        {/* LOGOUT button */}
        <Pressable
          onPress={() => {
            logout();
            router.replace("/login");
          }}
          className="flex-row items-center justify-center py-3 px-4 rounded-md bg-red-600 w-full"
          android_ripple={{ color: "#fecaca" }}
        >
          <Text className="text-red-600 font-semibold uppercase">Logout</Text>
          {/* you can swap this for any icon (lucide, expo vector icons, etc.) */}
        </Pressable>
      </View>

      <View className="flex-1" />
    </PageView>
  );
}
