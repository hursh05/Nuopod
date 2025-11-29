import { PageView, View } from "@/components/Themed";
import { urls } from "@/constants/urls";
import request from "@/services/api/request";
import { useAuthStore } from "@/store/useAuthStore";
import Feather from "@expo/vector-icons/Feather";
import { useRouter } from "expo-router";
import React, { useEffect, useState } from "react";
import { ActivityIndicator, Dimensions, Pressable, ScrollView, Text } from "react-native";
import { BarChart } from "react-native-chart-kit";

const screenWidth = Dimensions.get("window").width;

type FinancialInsights = {
  analysisDate: string | null;
  analysisPeriodDays: number;
  avgDailyIncome: number;
  avgDailyExpense: number;
  avgDailySavings: number;
  savingsRate: number;
  totalSavingsLast30Days: number;
  incomeStability: string | null;
  incomeStabilityScore: number;
  expenseStability: string | null;
  topExpenseCategory: string | null;
  topExpenseCategoryAmount: number;
  topExpenseCategoryPercent: number;
  unnecessarySpendingAmount: number;
  avgDailyBalance: number;
  lowestBalance: number;
  lowestBalanceDate: string | null;
  daysWithNegativeCashflow: number;
  daysWithLowBalance: number;
  cashCrunchRisk: string | null;
  impulsivePurchases: number;
  spendingPatternType: string | null;
  averageTransactionSize: number;
  highValueTransactions: number;
  overallRiskLevel: string | null;
  riskScore: number;
  riskFactors: string[];
  strengths: string[];
  weaknesses: string[];
  recommendedDailySavings: number;
  recommendedEmergencyFund: number;
  monthsToEmergencyFund: number;
  spendingPeakDay: string | null;
  spendingPeakTime: string | null;
  budgetAdherence: number;
  predictedShortfallDays: number;
  predictedShortfallAmount: number;
  nextLowBalanceDate: string | null;
  financialHealthGrade: string | null;
  insightsSummary: string | null;
};

const chartConfig = {
  backgroundGradientFrom: "#171717",
  backgroundGradientTo: "#171717",
  decimalPlaces: 0,
  color: (opacity = 1) => `rgba(255,255,255,${opacity})`,
  labelColor: (opacity = 1) => `rgba(200,200,200,${opacity})`,
  propsForBackgroundLines: {
    stroke: "#27272a",
  },
};

export default function FinancialInsightsDetailsScreen() {
    const router = useRouter();
  const [data, setData] = useState<FinancialInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isLoggedIn } = useAuthStore();

  const fetchData = async () => {
    try {
      setLoading(true);
      const { data, HttpStatusCode, status } = await request<any>(
        "GET",
        urls.auth.financial_insights,
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
    if (isLoggedIn) fetchData();
  }, [isLoggedIn]);

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
        <Text className="text-red-400 mb-1">
          Error loading financial insights
        </Text>
        <Text className="text-white text-xs">{error}</Text>
      </PageView>
    );
  }

  const incomeExpenseSavingsChart = {
    labels: ["Income", "Expense", "Savings"],
    datasets: [
      {
        data: [data.avgDailyIncome, data.avgDailyExpense, data.avgDailySavings],
      },
    ],
  };

  const savingsEmergencyChart = {
    labels: ["30D Savings", "Emergency Fund"],
    datasets: [
      {
        data: [data.totalSavingsLast30Days, data.recommendedEmergencyFund],
      },
    ],
  };

  const riskShortfallChart = {
    labels: ["Shortfall Days", "Shortfall Amount"],
    datasets: [
      {
        data: [data.predictedShortfallDays, data.predictedShortfallAmount],
      },
    ],
  };

  const analysisDateStr = data.analysisDate
    ? new Date(data.analysisDate).toDateString()
    : null;

  return (
    <PageView className="flex justify-center items-center px-2">
      <ScrollView className="flex-1 bg-black px-2 pt-4 w-full">
        {/* header */}
        <View className="flex-row items-center justify-start my-2 gap-x-8 w-full">
          <Pressable
            className="flex-row items-center justify-center"
            onPress={() => router.back()}
          >
            <Feather name="arrow-left" size={22} color={"#fff"} />
            {/* <Text className="text-xs font-semibold text-white">Go back</Text> */}
          </Pressable>
          <Text className="text-white text-xl font-semibold">
            Financial Insights
          </Text>
        </View>

        

        {analysisDateStr && (
          <Text className="text-neutral-500 text-sm mt-2">
            Based on last {data.analysisPeriodDays} days · {analysisDateStr}
          </Text>
        )}

        <View className="flex-row items-center gap-2 mt-2">
          {data.financialHealthGrade && (
            <View className="bg-neutral-900 px-2 py-1 rounded-lg">
              <Text className="text-neutral-200 text-sm">
                Grade: {data.financialHealthGrade}
              </Text>
            </View>
          )}
          {data.overallRiskLevel && (
            <View className="bg-neutral-900 px-2 py-1 rounded-lg">
              <Text  className={`text-neutral-200 text-sm`}>
                Risk: <Text className={`${data.overallRiskLevel === "low" ? "text-green-500" : data.overallRiskLevel === "medium" ? "text-yellow-500" : "text-red-500"} text-sm`}>{data.overallRiskLevel}</Text>
              </Text>
            </View>
          )}
        </View>

        {data.insightsSummary && (
          <View className="bg-neutral-900 rounded-2xl p-3 mb-4">
            <Text className="text-neutral-200 text-sm mb-1">Summary</Text>
            <Text className="text-neutral-400 text-xs">
              {data.insightsSummary}
            </Text>
          </View>
        )}

        {/* chart 1: Income vs Expense vs Savings */}
        <View className="bg-neutral-900 rounded-2xl p-3 mb-4">
          <Text className="text-neutral-200 text-sm mb-2">
            Income vs Expense vs Savings (Daily Avg)
          </Text>
          <BarChart
            data={incomeExpenseSavingsChart}
            width={screenWidth - 60}
            height={220}
            chartConfig={chartConfig}
            fromZero
            showValuesOnTopOfBars
            yAxisLabel="₹"
            yAxisSuffix=""
            style={{ borderRadius: 16 }}
          />
        </View>

        {/* chart 2: Savings vs Emergency fund */}
        <View className="bg-neutral-900 rounded-2xl p-3 mb-4">
          <Text className="text-neutral-200 text-sm mb-2">
            Savings vs Recommended Emergency Fund
          </Text>
          <BarChart
            data={savingsEmergencyChart}
            width={screenWidth - 60}
            height={220}
            chartConfig={chartConfig}
            fromZero
            showValuesOnTopOfBars
            yAxisLabel="₹"
            yAxisSuffix=""
            style={{ borderRadius: 16 }}
          />
          <Text className="text-neutral-400 text-xs mt-2">
            Months to full emergency fund:{" "}
            {data.monthsToEmergencyFund.toFixed(1)}
          </Text>
        </View>

        {/* chart 3: Shortfall & risk */}
        <View className="bg-neutral-900 rounded-2xl p-3 mb-4">
          <Text className="text-neutral-200 text-sm mb-2">
            Shortfall Risk Overview
          </Text>
          <BarChart
            data={riskShortfallChart}
            width={screenWidth - 60}
            height={220}
            chartConfig={chartConfig}
            fromZero
            showValuesOnTopOfBars
            style={{ borderRadius: 16 }}
            yAxisLabel=""
  yAxisSuffix=""     
          />
          <Text className="text-neutral-400 text-xs mt-2">
            Negative cashflow days: {data.daysWithNegativeCashflow}
          </Text>
          <Text className="text-neutral-400 text-xs">
            Cash crunch risk: {data.cashCrunchRisk || "N/A"}
          </Text>
          {data.nextLowBalanceDate && (
            <Text className="text-red-400 text-xs mt-1">
              Next expected low balance:{" "}
              {new Date(data.nextLowBalanceDate).toDateString()}
            </Text>
          )}
        </View>

        {/* spending behaviour */}
        <View className="bg-neutral-900 rounded-2xl p-3 mb-4">
          <Text className="text-neutral-200 text-sm mb-1">
            Spending Behaviour
          </Text>
          <Text className="text-neutral-400 text-xs">
            Pattern: {data.spendingPatternType || "N/A"}
          </Text>
          {data.topExpenseCategory && (
            <Text className="text-neutral-400 text-xs mt-1">
              Top category: {data.topExpenseCategory} · ₹
              {data.topExpenseCategoryAmount.toFixed(0)} (
              {data.topExpenseCategoryPercent.toFixed(1)}%)
            </Text>
          )}
          <Text className="text-neutral-400 text-xs mt-1">
            Unnecessary spends: ₹{data.unnecessarySpendingAmount.toFixed(0)}
          </Text>
          <Text className="text-neutral-400 text-xs mt-1">
            Avg txn size: ₹{data.averageTransactionSize.toFixed(0)} · High value
            txns: {data.highValueTransactions}
          </Text>
          <Text className="text-neutral-400 text-xs mt-1">
            Impulsive purchases: {data.impulsivePurchases}
          </Text>
          {data.spendingPeakDay && (
            <Text className="text-neutral-400 text-xs mt-1">
              Peak spend: {data.spendingPeakDay} ({data.spendingPeakTime})
            </Text>
          )}
        </View>

        {/* strengths / weaknesses / risk factors */}
        <View className="bg-neutral-900 rounded-2xl p-3 mb-4">
          <Text className="text-neutral-200 text-sm mb-2">Strengths</Text>
          {data.strengths.length > 0 ? (
            data.strengths.map((s, i) => (
              <Text key={i} className="text-emerald-400 text-xs mb-1">
                • {s}
              </Text>
            ))
          ) : (
            <Text className="text-neutral-500 text-xs">
              No strengths recorded.
            </Text>
          )}

          <Text className="text-neutral-200 text-sm mt-3 mb-2">Weaknesses</Text>
          {data.weaknesses.length > 0 ? (
            data.weaknesses.map((w, i) => (
              <Text key={i} className="text-red-400 text-xs mb-1">
                • {w}
              </Text>
            ))
          ) : (
            <Text className="text-neutral-500 text-xs">
              No weaknesses recorded.
            </Text>
          )}

          <Text className="text-neutral-200 text-sm mt-3 mb-2">
            Risk Factors
          </Text>
          {data.riskFactors.length > 0 ? (
            data.riskFactors.map((r, i) => (
              <Text key={i} className="text-amber-400 text-xs mb-1">
                • {r}
              </Text>
            ))
          ) : (
            <Text className="text-neutral-500 text-xs">
              No risk factors recorded.
            </Text>
          )}
        </View>
      </ScrollView>
    </PageView>
  );
}
