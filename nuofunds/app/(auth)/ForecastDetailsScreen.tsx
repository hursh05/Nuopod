import { PageView, Text, View } from "@/components/Themed";
import { urls } from "@/constants/urls";
import request from "@/services/api/request";
import { useAuthStore } from "@/store/useAuthStore";
import Feather from "@expo/vector-icons/Feather";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Dimensions,
  Pressable,
  ScrollView,
} from "react-native";
import { LineChart } from "react-native-chart-kit";

const screenWidth = Dimensions.get("window").width;

const COLORS = {
  income: "#4CAF50",
  expense: "#FF5252",
  shortfall: "#2196F3",
};

type ForecastEntry = {
  date: string;
  predictedIncome: number;
  predictedExpense: number;
  predictedShortfall: number;
  riskLevel: string;
};

type ForecastResponse = {
  days: number;
  entries: ForecastEntry[];
};

function formatDate(d: string) {
  const dt = new Date(d);
  const dd = String(dt.getDate()).padStart(2, "0");
  const mm = String(dt.getMonth() + 1).padStart(2, "0");
  return `${dd}/${mm}/${String(dt.getFullYear()).slice(-2)}`; // yyyy-mm-dd
}

export default function ForecastDetailsScreen() {
  const router = useRouter();
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isLoggedIn } = useAuthStore();

  const fetchApi = async () => {
    try {
      setLoading(true);
      const { data, HttpStatusCode, status } = await request<any>(
        "GET",
        urls.auth.forecast_details,
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
    if (isLoggedIn) fetchApi();
  }, [isLoggedIn]);

  if (loading)
    return (
      <PageView className="flex justify-center items-center bg-black">
        <ActivityIndicator />
      </PageView>
    );

  if (error || !data)
    return (
      <PageView className="flex justify-center items-center bg-black px-4">
        <Text className="text-red-400">Error loading forecast</Text>
      </PageView>
    );

  const labels = data.entries.map((e) => formatDate(e.date));
  const income = data.entries.map((e) => e.predictedIncome);
  const expense = data.entries.map((e) => e.predictedExpense);
  const shortfall = data.entries.map((e) => e.predictedShortfall);

  const chartData = {
    labels,
    datasets: [
      { data: income, color: () => COLORS.income, strokeWidth: 2 },
      { data: expense, color: () => COLORS.expense, strokeWidth: 2 },
      { data: shortfall, color: () => COLORS.shortfall, strokeWidth: 2 },
    ],
    legend: ["Income", "Expense", "Shortfall"],
  };

  const chartConfig = {
    backgroundGradientFrom: "#171717",
    backgroundGradientTo: "#171717",
    decimalPlaces: 0,
    color: (o = 1) => `rgba(255,255,255,${o})`,
    labelColor: (o = 1) => `rgba(200,200,200,${o})`,
    propsForDots: { r: "3" },
  };

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
          <Text className="text-xl font-semibold">7-Day Forecast Summary</Text>
        </View>

        <Text className="text-grey-500 text-sm mt-4">
          Predicted incomes, expenses & cashflow risk
        </Text>

        {/* Legend */}
        <View className="flex-row gap-4 mb-2 mt-4">
          <View className="flex-row items-center gap-1">
            <View
              style={{
                width: 10,
                height: 10,
                backgroundColor: COLORS.income,
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
                backgroundColor: COLORS.expense,
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
                backgroundColor: COLORS.shortfall,
                borderRadius: 5,
              }}
            />
            <Text className="text-blue-400 text-[11px]">Shortfall</Text>
          </View>
        </View>

        {/* Chart */}
        <View className="bg-neutral-900 p-3 rounded-2xl mb-4">
          <LineChart
            data={chartData}
            width={screenWidth - 60}
            height={320}
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
        </View>

        {/* List */}
        {data.entries.map((e) => {
          const d = new Date(e.date).toDateString();
          return (
            <View
              key={e.date}
              className="bg-neutral-900 rounded-xl p-3 mb-2 flex-row justify-between"
            >
              <View>
                <Text className="text-white text-xs">{d}</Text>
                <Text className="text-neutral-400 text-[10px] mt-1">
                  Risk: {e.riskLevel}
                </Text>
              </View>

              <View className="items-end">
                <Text className="text-emerald-400 text-[11px]">
                  Income ₹{e.predictedIncome.toFixed(0)}
                </Text>
                <Text className="text-red-400 text-[11px]">
                  Expense ₹{e.predictedExpense.toFixed(0)}
                </Text>
                <Text className="text-blue-400 text-[11px] mt-1">
                  Shortfall {e.predictedShortfall >= 0 ? "+" : ""}
                  {e.predictedShortfall.toFixed(0)}
                </Text>
              </View>
            </View>
          );
        })}
      </ScrollView>
    </PageView>
  );
}
