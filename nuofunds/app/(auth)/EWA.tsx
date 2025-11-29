import { PageView, Text, View } from "@/components/Themed";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import React from "react";
import { ScrollView, TouchableOpacity } from "react-native";

const points = [
  "Access a portion of your earned salary before payday.",
  "Avoid payday loans, credit card interest and overdraft charges.",
  "Handle medical, family or emergency expenses without stress.",
  "Improves financial flexibility, morale and stability.",
];

export default function EWAScreen() {
  return (
    <PageView className="flex-1 bg-black">
      <ScrollView className="flex-1 px-4 pt-4">
        {/* header */}
        <View className="flex-row items-center mb-4">
          <TouchableOpacity
            onPress={() => router.back()}
            className="mr-3 pr-1 py-1"
            activeOpacity={0.7}
          >
            <Ionicons name="chevron-back" size={22} color="#e5e5e5" />
          </TouchableOpacity>
          <View className="flex-1">
            <Text className="text-white text-lg font-semibold">
              Earned Wage Access (EWA)
            </Text>
            <Text className="text-neutral-500 text-[11px]">
              Access part of your salary before payday — on demand.
            </Text>
          </View>
        </View>

        {/* hero card */}
        <View className="bg-neutral-900 rounded-2xl p-4 mb-4 flex-row items-center">
          <View className="flex-1 mr-3">
            <Text className="text-white text-lg font-semibold mb-1">
              Salary when you actually need it
            </Text>
            <Text className="text-neutral-400 text-xs">
              EWA lets you withdraw already-earned wages early to handle
              real-life cash crunches — without high-interest credit.
            </Text>
          </View>
          <View className="w-16 h-16 rounded-2xl bg-sky-900/40 items-center justify-center">
            <Text className="text-3xl">⚡</Text>
          </View>
        </View>

        {/* benefits */}
        <View className="bg-neutral-900 rounded-2xl p-4 mb-4">
          <Text className="text-neutral-200 text-lg mb-2 font-bold">
            How EWA helps you
          </Text>

          {points?.map((item, idx) => (
            <View key={idx} className="flex-row items-center mb-2">
              <Ionicons
                name="checkmark-circle"
                size={16}
                color="#38bdf8"
                style={{ marginTop: 2, marginRight: 6 }}
              />
              <Text className="text-neutral-300 text-xs flex-1">{item}</Text>
            </View>
          ))}
        </View>

        {/* how it will work on NuoFunds */}
        <View className="bg-neutral-900 rounded-2xl p-4 mb-4">
          <Text className="text-neutral-200 text-lg mb-2 font-bold">
            How EWA on NuoFunds will work
          </Text>

          <View className="bg-neutral-950 rounded-xl mb-2">
            <Text className="text-neutral-400 text-[14px] mb-1">
              1. Link your employer / EWA provider
            </Text>
            <Text className="!text-gray-300 text-xs">
              Your company partners with an EWA provider. You link your
              employment account securely inside NuoFunds.
            </Text>
          </View>

          <View className="bg-neutral-950 rounded-xl mb-2">
            <Text className="text-neutral-400 text-[14px] mb-1">
              2. See your available earned wages
            </Text>
            <Text className="!text-gray-300 text-xs">
              We show your safe-to-withdraw amount based on days worked and your
              salary structure.
            </Text>
          </View>

          <View className="bg-neutral-950 rounded-xl mb-1">
            <Text className="text-neutral-400 text-[14px] mb-1">
              3. Withdraw with context
            </Text>
            <Text className="!text-gray-300 text-xs">
              Before you withdraw, NuoFunds explains how it impacts your
              month-end cashflow, bills and savings goals.
            </Text>
          </View>
        </View>

        {/* safety / responsible use */}
        <View className="bg-neutral-900 rounded-2xl p-4 mb-4">
          <Text className="text-neutral-200 text-lg mb-2 font-bold">
            Designed for responsible use
          </Text>
          <Text className="text-neutral-400 text-xs mb-1">
            EWA is not a loan. It&apos;s your own earned salary — but early.
          </Text>
          <Text className="text-neutral-400 text-xs mb-1">
            We&apos;ll combine EWA with your spending & savings insights so you
            don&apos;t slip into a constant advance cycle.
          </Text>
          <Text className="text-neutral-400 text-xs">
            Smart nudges will warn you if frequent EWA use is creating long-term
            cashflow issues.
          </Text>
        </View>

        {/* CTA */}
        <View className="mb-8">
          <Text className="text-neutral-400 text-[11px] mb-2">
            Coming soon with selected employer and provider partners.
          </Text>
          <TouchableOpacity
            disabled
            activeOpacity={0.8}
            className="bg-sky-600/90 rounded-2xl py-3 items-center"
          >
            <Text className="text-white text-xs font-semibold tracking-wide">
              Get Early Access to EWA (Soon)
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </PageView>
  );
}
