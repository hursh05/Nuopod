import { PageView, Text, View } from "@/components/Themed";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import React from "react";
import { ScrollView, TouchableOpacity } from "react-native";

const points = [
  "Get a personalised plan from your actual bank data.",
  "Turn NuoFunds insights into concrete actions.",
  "Optimise loans, investments, taxes & emergency fund.",
  "Stay accountable with regular check-ins.",
];

export default function AdvisorConnectScreen() {
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
              Advisor Connect
            </Text>
            <Text className="text-neutral-500 text-[11px]">
              Hire a financial expert to level up your money decisions.
            </Text>
          </View>
        </View>

        {/* hero card */}
        <View className="bg-neutral-900 rounded-2xl p-4 mb-4 flex-row items-center">
          <View className="flex-1 mr-3">
            <Text className="text-white text-base font-semibold mb-1">
              Work with a real financial advisor
            </Text>
            <Text className="text-neutral-400 text-xs">
              Turn your insights into an actual plan — tailored to your goals,
              risk appetite and cashflow.
            </Text>
          </View>
          <View className="w-16 h-16 rounded-2xl bg-emerald-900/40 items-center justify-center">
            <Text className="text-3xl">👩‍💼</Text>
          </View>
        </View>

        {/* why you need an advisor */}
        <View className="bg-neutral-900 rounded-2xl p-4 mb-4">
          <Text className="text-neutral-200 text-lg mb-2">
            Why connect with an advisor?
          </Text>

          {points?.map((item, idx) => (
            <View key={idx} className="flex-row items-center mb-2">
              <Ionicons
                name="checkmark-circle"
                size={16}
                color="#22c55e"
                style={{ marginTop: 2, marginRight: 6 }}
              />
              <Text className="text-neutral-300 text-xs flex-1">{item}</Text>
            </View>
          ))}
        </View>

        {/* what you get section */}
        <View className="bg-neutral-900 rounded-2xl p-4 mb-4">
          <Text className="text-neutral-200 text-lg mb-2">
            What your advisor can help with
          </Text>

          <View className="flex-row justify-between mb-2">
            <View className="w-[48%] bg-neutral-950 rounded-xl p-3 border border-neutral-800">
              <Text className="text-neutral-400 text-[14px] mb-1">
                Cashflow & budgeting
              </Text>
              <Text className="!text-gray-300 text-xs">
                Fix overspending, build a realistic monthly plan and stick to
                it.
              </Text>
            </View>
            <View className="w-[48%] bg-neutral-950 rounded-xl p-3 border border-neutral-800">
              <Text className="text-neutral-400 text-[14px] mb-1">
                Investments & goals
              </Text>
              <Text className="!text-gray-300 text-xs">
                Map your investments to goals like house, travel or early
                retirement.
              </Text>
            </View>
          </View>

          <View className="flex-row justify-between">
            <View className="w-[48%] bg-neutral-950 rounded-xl p-3 border border-neutral-800">
              <Text className="text-neutral-400 text-[14px] mb-1">
                Risk & protection
              </Text>
              <Text className="!text-gray-300 text-xs">
                Right level of insurance + emergency fund so life shocks
                don&apos;t break you.
              </Text>
            </View>
            <View className="w-[48%] bg-neutral-950 rounded-xl p-3 border border-neutral-800">
              <Text className="text-neutral-400 text-[14px] mb-1">
                Ongoing guidance
              </Text>
              <Text className="!text-gray-300 text-xs">
                Quarterly reviews based on your latest NuoFunds data.
              </Text>
            </View>
          </View>
        </View>

        {/* CTA */}
        <View className="mb-8">
          <Text className="text-neutral-400 text-[11px] mb-2">
            Coming soon: verified SEBI-registered advisors on NuoFunds.
          </Text>
          <TouchableOpacity
            disabled
            activeOpacity={0.8}
            className="bg-purple-600/90 rounded-2xl py-3 items-center"
          >
            <Text className="text-white text-xs font-semibold tracking-wide">
              Hire an Advisor (Soon)
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </PageView>
  );
}
