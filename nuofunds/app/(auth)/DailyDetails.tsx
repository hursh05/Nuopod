import { PageView, Text, View } from "@/components/Themed";
import { urls } from "@/constants/urls";
import request from "@/services/api/request";
import { useAuthStore } from "@/store/useAuthStore";
import Feather from "@expo/vector-icons/Feather";
import { useRouter } from "expo-router";
import React, { useEffect, useState } from "react";
import { ActivityIndicator, Dimensions, Pressable, ScrollView } from "react-native";
import { LineChart } from "react-native-chart-kit";

type DailyPoint = {
  date: string;
  totalIncome: number;
  totalExpense: number;
  netAmount: number;
  closingBalance: number | null;
  transactionCount: number;
};

type DailyDetailsResponse = {
  days: number;
  points: DailyPoint[];
};

const screenWidth = Dimensions.get("window").width;

const LINE_COLORS = {
  income: "#4CAF50", // green
  expense: "#FF5252", // red
  net: "#2196F3", // blue
};

const chartConfig = {
  backgroundGradientFrom: "#171717",
  backgroundGradientTo: "#171717",
  decimalPlaces: 0,
  color: (opacity = 1) => `rgba(255,255,255,${opacity})`,
  labelColor: (opacity = 1) => `rgba(200,200,200,${opacity})`,
  propsForDots: {
    r: "3",
  },
  propsForBackgroundLines: {
    stroke: "#27272a",
  },
  propsForLabels: {
    fontSize: 8,
  },
};

function formatLabel(dateStr: string) {
  const d = new Date(dateStr);
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  return `${dd}/${mm}/${String(d.getFullYear()).slice(-2)}`; // yyyy-mm-dd
}

export default function DailyDetailsScreen() {
  const [data, setData] = useState<DailyDetailsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isLoggedIn } = useAuthStore();

  const fetchData = async () => {
    try {
      setLoading(true);
      const { data, HttpStatusCode, status } = await request<any>(
        "GET",
        urls.auth.daily_details,
        {
          days: 7, // ask backend for last 30 records
        },
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
        <Text className="text-red-400 mb-1">error loading daily details</Text>
        <Text className="text-white text-xs">{error}</Text>
      </PageView>
    );
  }

  const hasEnoughPoints = data.points.length > 1;

  // x-axis labels = actual dates
  const labels = data.points.map((p) => formatLabel(p.date));

  // y values
  const income = data.points.map((p) => Number(p.totalIncome || 0));
  const expense = data.points.map((p) => Number(p.totalExpense || 0));
  const net = data.points.map((p) => Number(p.netAmount || 0));

  const chartData = {
    labels,
    datasets: [
      {
        data: income,
        color: () => LINE_COLORS.income,
        strokeWidth: 2,
      },
      {
        data: expense,
        color: () => LINE_COLORS.expense,
        strokeWidth: 2,
      },
      {
        data: net,
        color: () => LINE_COLORS.net,
        strokeWidth: 2,
      },
    ],
    legend: ["Income", "Expense", "Net"],
  };

  const firstDate = data.points[0]?.date;
  const lastDate = data.points[data.points.length - 1]?.date;
  const router = useRouter();

  return (
    <PageView className="flex justify-center items-center px-2">
      <ScrollView className="flex-1 bg-black px-4 pt-4 w-full">
        <View className="flex-row items-center justify-start my-1 gap-x-8">
          <Pressable
            className="flex-row items-center justify-center"
            onPress={() => router.back()}
          >
            <Feather name="arrow-left" size={22} color={"#fff"} />
            {/* <Text className="text-xs font-semibold">Go back</Text> */}
          </Pressable>
          <Text className="text-xl font-semibold">Recent Summary & Trends</Text>
        </View>


        <View className="mt-4">
          <Text className="text-neutral-500 text-sm my-2">
          Daily income, expenses and net amount over the last {data.days} days
        </Text>
        {firstDate && lastDate && (
          <Text className="text-neutral-600 text-sm mb-4">
            From {formatLabel(firstDate)} to {formatLabel(lastDate)}
          </Text>
        )}
        </View>

        <View className="bg-neutral-900 rounded-2xl p-3 mb-4">
          {/* custom legend */}
          <View className="flex-row gap-4 mb-2">
            <View className="flex-row items-center gap-1">
              <View
                style={{
                  width: 10,
                  height: 10,
                  backgroundColor: LINE_COLORS.income,
                  borderRadius: 5,
                }}
              />
              <Text className="text-emerald-400 text-[11px]">Income</Text>
            </View>

            <View className="flex-row items-center gap-1">
              <View
                style={{
                  width: 10,
                  height: 10,
                  backgroundColor: LINE_COLORS.expense,
                  borderRadius: 5,
                }}
              />
              <Text className="text-red-400 text-[11px]">Expense</Text>
            </View>

            <View className="flex-row items-center gap-1">
              <View
                style={{
                  width: 10,
                  height: 10,
                  backgroundColor: LINE_COLORS.net,
                  borderRadius: 5,
                }}
              />
              <Text className="text-blue-400 text-[11px]">Net</Text>
            </View>
          </View>

          {hasEnoughPoints ? (
            <LineChart
              data={chartData}
              width={screenWidth - 60}
              height={280}
              chartConfig={chartConfig}
              bezier
              style={{ borderRadius: 16 }}
              withInnerLines
              withOuterLines={false}
              yAxisLabel="₹"
              verticalLabelRotation={45}
              withVerticalLabels
              withHorizontalLabels
            />
          ) : (
            <Text className="text-neutral-400 text-xs">
              Not enough data points to draw chart yet
            </Text>
          )}
        </View>

        {data?.points
          ?.slice()
          ?.reverse()
          ?.map((p) => {
            const d = new Date(p.date);
            return (
              <View
                key={p.date}
                className="bg-neutral-900 rounded-xl p-3 mb-2 flex-row justify-between"
              >
                <View>
                  <Text className="text-white text-xs">{d.toDateString()}</Text>
                  <Text className="text-neutral-400 text-[11px] mt-1">
                    Txns: {p.transactionCount}
                  </Text>
                </View>
                <View className="items-end">
                  <Text className="text-emerald-400 text-[11px]">
                    Income ₹{p.totalIncome.toFixed(0)}
                  </Text>
                  <Text className="text-red-400 text-[11px]">
                    Expense ₹{p.totalExpense.toFixed(0)}
                  </Text>
                  <Text
                    className={`text-[11px] mt-1 ${
                      p.netAmount >= 0 ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    Net {p.netAmount >= 0 ? "+" : ""}
                    {p.netAmount.toFixed(0)}
                  </Text>
                </View>
              </View>
            );
          })}
      </ScrollView>
    </PageView>
  );
}
