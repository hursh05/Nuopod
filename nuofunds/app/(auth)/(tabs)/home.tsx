import { PageView, View } from "@/components/Themed";
import { urls } from "@/constants/urls";
import request from "@/services/api/request";
import { useAuthStore } from "@/store/useAuthStore";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { useRouter } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  Text,
  TouchableOpacity,
} from "react-native";

import { Dimensions } from "react-native";
import { PieChart } from "react-native-chart-kit";

type HomeResponse = {
  dailySummary: {
    date: string;
    totalIncome: number;
    totalExpense: number;
    netAmount: number;
    closingBalance: number | null;
  } | null;
  forecastSummary: {
    fromDate: string;
    toDate: string;
    predictedIncome: number;
    predictedExpense: number;
    predictedShortfall: number;
    highestRiskDay: {
      date: string;
      riskLevel: string;
    } | null;
  } | null;
  expenseSummary: {
    period: "30d";
    totalExpense: number;
    topCategories: {
      category: string;
      amount: number;
      percent: number;
    }[];
  } | null;
  actionCards: {
    id: string;
    title: string;
    message: string;
    priority: string;
    category: string | null;
    expectedSavings: number | null;
    daysUntilImpact: number | null;
  }[];
  streakSummary: {
    totalActiveStreaks: number;
    topStreak?: {
      streakType: string;
      currentStreak: number;
      longestStreak: number;
      nextMilestone: number | null;
    };
  } | null;
  financialInsights: {
    overallRiskLevel: string | null;
    avgDailyIncome: number;
    avgDailyExpense: number;
    savingsRate: number;
    totalSavingsLast30Days: number;
    financialHealthGrade: string | null;
    insightsSummary: string | null;
  } | null;
};

const CLASSIC_COLORS = [
  "#4CAF50", // green
  "#2196F3", // blue
  "#FFC107", // amber
  "#FF5722", // deep orange
  "#9C27B0", // purple
  "#E91E63", // pink
  "#00BCD4", // cyan
  "#8BC34A", // light green
  "#FF9800", // orange
  "#3F51B5", // indigo
];

const screenWidth = Dimensions.get("window").width;

export default function HomeScreen() {
  const router = useRouter();
  const [data, setData] = useState<HomeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isLoggedIn } = useAuthStore();

  const fetchData = async () => {
    try {
      setLoading(true);
      const { data, HttpStatusCode, status } = await request<HomeResponse>(
        "GET",
        urls.auth.dashboard,
        {},
        {}
      );

      if (HttpStatusCode.OK === status && data.success) {
        setData(data.data);
      }
    } catch (e: any) {
      setError(e.message || "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isLoggedIn) {
      fetchData();
    }
  }, []);

  if (loading) {
    return (
      <PageView className="flex justify-center items-center bg-black">
        <ActivityIndicator />
      </PageView>
    );
  }

  if (error || !data) {
    return (
      <PageView className="flex justify-center items-center bg-black px-4">
        <Text className="text-red-400 mb-2">error loading dashboard</Text>
        <Text className="text-white text-xs">{error}</Text>
      </PageView>
    );
  }

  const {
    dailySummary,
    forecastSummary,
    expenseSummary,
    actionCards,
    streakSummary,
    financialInsights,
  } = data;

  const expenseChartConfig = {
    backgroundGradientFrom: "#171717",
    backgroundGradientTo: "#171717",
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(255,255,255,${opacity})`,
    labelColor: (opacity = 1) => `rgba(229,229,229,${opacity})`,
  };

  return (
    <PageView className="flex justify-center items-center px-2">
      <View className="w-full flex-row items-center justify-between bg-black px-4 py-2 mt-4 ">
        <Text className="text-white text-2xl !font-[900] tracking-tighter">Nuofund</Text>

        <TouchableOpacity>
          <MaterialCommunityIcons name="bell" size={24} color="white" />
        </TouchableOpacity>
      </View>
      <ScrollView
        className="flex-1 bg-black px-4 pt-4 w-full"
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={() => fetchData()} />
        }
      >
        {/* daily summary card */}
        <View
          className="mb-4 rounded-2xl p-4 bg-neutral-900 inset-shadow-sm border border-neutral-800"
          
        >
          <Text className="text-neutral-200 text-lg mb-1">
            Today&apos;s Money Summary
          </Text>

          <Text className="text-neutral-500 text-sm mb-2">
            Your income, expenses & balance for today
          </Text>

          {dailySummary ? (
            <>
              <Text className="text-white text-lg font-semibold">
                Income ₹{dailySummary.totalIncome.toFixed(0)} · Expense ₹
                {dailySummary.totalExpense.toFixed(0)}
              </Text>

              <Text
                className={`mt-1 text-sm ${
                  dailySummary.netAmount >= 0
                    ? "text-emerald-400"
                    : "text-red-400"
                }`}
              >
                Net {dailySummary.netAmount >= 0 ? "+" : ""}
                {dailySummary.netAmount.toFixed(0)}
              </Text>

              {dailySummary.closingBalance !== null && (
                <Text className="text-neutral-500 text-xs mt-1">
                  Closing balance: ₹{dailySummary.closingBalance.toFixed(0)}
                </Text>
              )}
            </>
          ) : (
            <>
              <Text className="text-neutral-300 text-sm">
                No summary available for today yet.
              </Text>
              <Text className="text-neutral-500 text-[12px] mt-1">
                Tap to view your recent days & detailed trends.
              </Text>
            </>
          )}

          {/* CTA button */}
          <View className="mt-4">
            <TouchableOpacity
              className="!bg-white py-2 rounded-lg items-center"
              style={{ opacity: 0.95 }}
              onPress={() => router.push("/(auth)/DailyDetails")}
            >
              <Text className="!text-black text-sm font-semibold">
                View Recent Activity →
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* forecast card */}
        <View
          className="mb-4 rounded-2xl p-4 bg-neutral-900 inset-shadow-sm border border-neutral-800"
        >
          <Text className="text-neutral-200 text-lg mb-1">
            Upcoming 7-Day Outlook
          </Text>
          <Text className="text-neutral-500 text-sm mb-2">
            Predicted income, expenses & cash risk
          </Text>

          {forecastSummary ? (
            <>
              <Text className="text-white text-lg font-semibold">
                Income:{" "}
                <Text className="text-green-500">
                  ₹{forecastSummary?.predictedIncome?.toFixed(0)}{" "}
                </Text>
                · Expense:{" "}
                <Text className="text-red-500">
                  ₹{forecastSummary?.predictedExpense?.toFixed(0)}
                </Text>
              </Text>

              <Text className="text-neutral-400 text-sm mt-1">
                Expected shortfall:&nbsp;
                <Text className="text-red-400">
                  ₹{forecastSummary?.predictedShortfall?.toFixed(0)}
                </Text>
              </Text>

              {forecastSummary.highestRiskDay && (
                <Text className="text-red-400 text-xs mt-1">
                  Highest risk on{" "}
                  {new Date(forecastSummary.highestRiskDay.date).toDateString()}{" "}
                  ({forecastSummary.highestRiskDay.riskLevel})
                </Text>
              )}
            </>
          ) : (
            <>
              <Text className="text-neutral-400 text-sm">
                No forecast available for the next 7 days yet.
              </Text>
              <Text className="text-neutral-500 text-[11px] mt-1">
                Tap to view your upcoming cashflow and risk once it&apos;s
                generated.
              </Text>
            </>
          )}

          {/* CTA button */}
          <View className="mt-4">
            <TouchableOpacity className="!bg-white py-2 rounded-lg items-center" onPress={() => router.push("/(auth)/ForecastDetailsScreen")}>
              <Text className="text-black text-sm font-semibold">
                View Forecast Details →
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* expense summary card */}
        <View
          className="mb-4 rounded-2xl p-4 bg-neutral-900 inset-shadow-sm border border-neutral-800"
        >
          <Text className="text-neutral-200 text-lg mb-1">
            Spending Breakdown (Last 30 Days)
          </Text>
          <Text className="text-neutral-500 text-[12px] mb-2">
            Your top spending categories this month
          </Text>

          {expenseSummary && expenseSummary.totalExpense > 0 ? (
            <>
              <Text className="text-white text-lg font-semibold mb-2">
                Total spends ₹{expenseSummary.totalExpense.toFixed(0)}
              </Text>

              {/* pie chart */}
              {expenseSummary.topCategories.length > 0 ? (
                <View className="items-center mb-2">
                  <PieChart
                    data={expenseSummary.topCategories.map((cat, idx) => ({
                      name: cat.category,
                      value: cat.amount,
                      color: CLASSIC_COLORS[idx % CLASSIC_COLORS.length],
                      legendFontColor: "#e5e5e5",
                      legendFontSize: 10,
                    }))}
                    width={screenWidth - 80}
                    height={180}
                    accessor="value"
                    backgroundColor="transparent"
                    chartConfig={expenseChartConfig}
                    hasLegend={true}
                    paddingLeft="0"
                    center={[0, 0]}
                  />
                </View>
              ) : null}

              {/* text rows under pie for quick read */}
              {expenseSummary.topCategories.slice(0, 3).map((cat) => (
                <Text
                  key={cat.category}
                  className="text-neutral-300 text-xs mt-1"
                >
                  {cat.category}: ₹{cat.amount.toFixed(0)} (
                  {cat.percent.toFixed(1)}%)
                </Text>
              ))}
            </>
          ) : (
            <>
              <Text className="text-neutral-400 text-base mb-1">
                No spending data available for the last 30 days.
              </Text>
              <Text className="text-neutral-500 text-[11px]">
                Once we detect your transactions, we&apos;ll show your
                category-wise spend here with a breakdown.
              </Text>
            </>
          )}
        </View>

        <View
          className="mb-4 rounded-2xl p-4 bg-neutral-900 inset-shadow-sm border border-neutral-800"
        >
          <Text className="text-neutral-200 text-lg mb-1">
            Financial Health Overview
          </Text>
          <Text className="text-neutral-300 text-[12px] mb-2">
            Snapshot of your last 30 days
          </Text>

          {financialInsights ? (
            <>
              <View className="w-full flex-row items-center justify-between gap-2 mb-2 !bg-gray-800 rounded-sm">
                {financialInsights?.financialHealthGrade && (
                  <View className="!bg-gray-800 px-2 py-1 rounded-lg">
                    <Text className="text-sm text-neutral-200">
                      Grade: {financialInsights?.financialHealthGrade}
                    </Text>
                  </View>
                )}
                {financialInsights?.overallRiskLevel && (
                  <View className="!bg-gray-800 px-2 py-1 rounded-lg">
                    <Text className="text-sm text-neutral-200">
                      Risk: <Text className={`${financialInsights?.overallRiskLevel === "low" ? "text-green-500" : financialInsights?.overallRiskLevel === "medium" ? "text-yellow-500" : "text-red-500"}`}>{financialInsights?.overallRiskLevel}</Text>
                    </Text>
                  </View>
                )}
              </View>

              <Text className="text-white text-base">
                Avg daily income:&nbsp;&nbsp;<Text className="text-green-500">₹{financialInsights?.avgDailyIncome.toFixed(0)}</Text>
              </Text>
              <Text className="text-white text-base">
                Avg daily expense:&nbsp;&nbsp;<Text className="text-red-500">₹{financialInsights?.avgDailyExpense.toFixed(0)}</Text>
              </Text>
              <Text className="text-emerald-400 text-sm mt-1">
                Savings rate: {financialInsights?.savingsRate.toFixed(1)}%
              </Text>

              {financialInsights?.totalSavingsLast30Days > 0 && (
                <Text className="text-neutral-400 text-xs mt-1">
                  Saved last 30 days: ₹
                  {financialInsights?.totalSavingsLast30Days.toFixed(0)}
                </Text>
              )}

              {financialInsights?.insightsSummary && (
                <Text className="text-neutral-500 text-[11px] mt-2">
                  {financialInsights?.insightsSummary}
                </Text>
              )}
            </>
          ) : (
            <>
              <Text className="text-neutral-400 text-sm">
                We haven&apos;t analysed your finances yet.
              </Text>
              <Text className="text-neutral-500 text-[11px] mt-1">
                Connect accounts and generate insights to see your overall
                financial health.
              </Text>
            </>
          )}

          <View className="mt-4">
            <TouchableOpacity className="!bg-white py-2 rounded-lg items-center" onPress={() => router.push("/(auth)/FinancialInsightsDetails")}>
              <Text className="!text-blac text-sm font-semibold">
                View Full Insights →
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* action cards */}
        {actionCards.length > 0 && (
          <View className="mb-4">
            <Text className="text-neutral-200 text-xl mb-1">
              Smart Suggestions For You
            </Text>
            <Text className="text-neutral-500 text-[14px] mb-2">
              Personalised actions to improve your finances
            </Text>

            {actionCards.map((card) => (
              <View
                key={card.id}
                className="mb-2 rounded-2xl p-3 border border-white/50"
              >
                <Text className="text-white text-sm font-semibold">
                  {card.title}
                </Text>
                <Text className="text-neutral-400 text-xs mt-1">
                  {card.message}
                </Text>
                {card.expectedSavings !== null && (
                  <Text className="text-emerald-400 text-xs mt-1">
                    Potential save: ₹{card.expectedSavings.toFixed(0)}
                  </Text>
                )}
              </View>
            ))}
          </View>
        )}

        {/* streak summary */}
        {streakSummary && streakSummary.topStreak && (
          <TouchableOpacity
            className="mb-8 rounded-2xl p-4 bg-neutral-900"
            onPress={() => {}}
          >
            <Text className="text-neutral-200 text-sm mb-1">
              Your Progress & Streaks
            </Text>
            <Text className="text-neutral-500 text-[10px] mb-2">
              How consistently you&apos;ve been saving or improving
            </Text>

            <Text className="text-white text-lg font-semibold">
              {streakSummary.topStreak.streakType} streak:{" "}
              {streakSummary.topStreak.currentStreak} days
            </Text>
            <Text className="text-neutral-400 text-xs mt-1">
              Best so far: {streakSummary.topStreak.longestStreak} days
            </Text>
            {streakSummary.topStreak.nextMilestone && (
              <Text className="text-emerald-400 text-xs mt-1">
                Next milestone at {streakSummary.topStreak.nextMilestone} days
              </Text>
            )}
          </TouchableOpacity>
        )}
      </ScrollView>
    </PageView>
  );
}
