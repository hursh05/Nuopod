import { PageView, Text, View } from "@/components/Themed";
import { urls } from "@/constants/urls";
import request from "@/services/api/request";
import Feather from "@expo/vector-icons/Feather";
import DateTimePicker, {
  DateTimePickerEvent,
} from "@react-native-community/datetimepicker";
import { useRouter } from "expo-router";
import React, { useState } from "react";
import {
  Modal,
  Platform,
  Pressable,
  ScrollView,
  TextInput,
} from "react-native";
import Toast from "react-native-toast-message";

const MODES = ["UPI", "FT", "CASH", "CARD", "OTHER"] as const;
const TYPES = ["DEBIT", "CREDIT"] as const;

export default function ManualTransactionScreen() {
  const router = useRouter();

  const [mode, setMode] = useState<(typeof MODES)[number]>("UPI");
  const [customMode, setCustomMode] = useState("");
  const [txType, setTxType] = useState<(typeof TYPES)[number]>("DEBIT");

  const [txnid, setTxnid] = useState("");
  const [amount, setAmount] = useState("");
  const [balance, setBalance] = useState("");
  const [comment, setComment] = useState("");
  const [date, setDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [loading, setLoading] = useState(false);

  const [modalVisible, setModalVisible] = useState(false);

  const onChangeDate = (event: DateTimePickerEvent, selected?: Date) => {
    if (Platform.OS === "android") setShowDatePicker(false);
    if (!selected) return;

    // keep old time, update Y/M/D
    const current = new Date(date);
    current.setFullYear(
      selected.getFullYear(),
      selected.getMonth(),
      selected.getDate()
    );
    setDate(current);

    // if you want auto-time picker after date pick:
    // setShowTimePicker(true);
  };

  // time change
  const onChangeTime = (event: DateTimePickerEvent, selected?: Date) => {
    if (Platform.OS === "android") setShowTimePicker(false);
    if (!selected) return;

    // keep old date, update H/M
    const current = new Date(date);
    current.setHours(selected.getHours());
    current.setMinutes(selected.getMinutes());
    setDate(current);
  };

  const handleSubmit = async () => {
    if (!mode.trim()) {
      Toast.show({
        type: "error",
        text1: "Mode required",
        text2: "Please select a mode.",
      });
      return;
    }

    if (mode === "OTHER" && !customMode.trim()) {
      Toast.show({
        type: "error",
        text1: "Custom mode required",
        text2: "Please enter a custom mode.",
      });
      return;
    }

    if (!txType.trim()) {
      Toast.show({
        type: "error",
        text1: "Type required",
        text2: "Please select a type.",
      });
      return;
    }

    if (!amount.trim()) {
      Toast.show({
        type: "error",
        text1: "Amount required",
        text2: "Please enter an amount.",
      });
      return;
    }

    setLoading(true);
    try {
      const { data, status, HttpStatusCode } = await request<any>(
        "POST",
        urls.auth.transactions.manual,
        {},
        {
          mode,
          customMode,
          type: txType,
          txnid: txnid.trim() || null,
          amount: amount.trim(),
          balance: balance.trim() || null,
          dateTime: date.toISOString(),
          comment: comment.trim() || null,
        }
      );

      if (status === HttpStatusCode.CREATED && data.success) {
        console.log("manual tx response:", data);
      } else {
        console.log("failed to save transaction");
      }
      // reset basic fields (optional)
      setTxnid("");
      setAmount("");
      setComment("");
      // show consent promo modal
      setModalVisible(true);
    } catch (e) {
      console.log("manual tx error:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageView className="flex-1 bg-white">
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
        keyboardShouldPersistTaps="handled"
      >
        <View className="flex-row items-center justify-start my-2 gap-x-8">
          <Pressable
            className="flex-row items-center justify-center"
            onPress={() => router.back()}
          >
            <Feather name="arrow-left" size={22} color={"#fff"} />
            {/* <Text className="text-xs font-semibold">Go back</Text> */}
          </Pressable>
          <Text className="text-xl font-semibold">Add manual transaction</Text>
        </View>

        {/* MODE */}
        <Text className="text-sm font-medium mb-2 mt-4">Mode</Text>
        <View className="flex-row flex-wrap mb-3">
          {MODES.map((m) => (
            <Pressable
              key={m}
              onPress={() => setMode(m)}
              className={`px-3 py-2 rounded-full mr-2 mb-2 border ${
                mode === m ? "bg-blue-600 border-blue-600" : "border-gray-700"
              }`}
            >
              <Text
                className={`text-sm ${
                  mode === m ? "text-white" : "text-gray-800"
                }`}
              >
                {m}
              </Text>
            </Pressable>
          ))}
        </View>

        {mode === "OTHER" && (
          <View className="mb-4">
            <Text className="text-sm font-medium mb-1">Custom mode</Text>
            <TextInput
              value={customMode}
              onChangeText={setCustomMode}
              placeholder="Enter mode name"
              className="border border-gray-700 rounded-md px-3 py-2 text-white"
            />
          </View>
        )}

        {/* TYPE */}
        <Text className="text-sm font-medium mb-2">Type</Text>
        {/* <View className="flex-row mb-4">
          {TYPES.map((t) => (
            <Pressable
              key={t}
              onPress={() => setTxType(t)}
              className={`px-3 py-2 rounded-full mr-2 border ${
                txType === 'CREDIT'
                  ? "bg-green-500 border-emerald-600"
                  : txType === 'DEBIT'
                    ? "bg-red-500 border-red-600"
                    : "border-gray-700"
              }`}
            >
              <Text
                className={`text-sm ${
                  txType === t ? "text-white" : "text-gray-800"
                }`}
              >
                {t}
              </Text>
            </Pressable>
          ))}
        </View> */}
        <View className="flex-row mb-4">
          {TYPES.map((t) => {
            const isSelected = txType === t;

            return (
              <Pressable
                key={t}
                onPress={() => setTxType(t)}
                className={`px-3 py-2 rounded-full mr-2 border 
          ${
            isSelected
              ? t === "CREDIT"
                ? "bg-green-500 border-green-600"
                : "bg-red-500 border-red-600"
              : "border-gray-700"
          }`}
              >
                <Text
                  className={`text-sm ${isSelected ? "text-white" : "text-gray-800"}`}
                >
                  {t}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* AMOUNT */}
        <View className="mb-4">
          <Text className="text-sm font-medium mb-1">Amount*</Text>
          <TextInput
            value={amount}
            onChangeText={setAmount}
            placeholder="0.00"
            placeholderTextColor={"#707070ff"}
            keyboardType="decimal-pad"
            className="border border-gray-700 rounded-md px-3 py-2 text-white"
          />
        </View>

        {/* TXN ID */}
        <View className="mb-4">
          <Text className="text-sm font-medium mb-1">
            Transaction ID (optional)
          </Text>
          <TextInput
            value={txnid}
            onChangeText={setTxnid}
            placeholder="UPI ref / card txn id"
            placeholderTextColor={"#707070ff"}
            className="border border-gray-700 rounded-md px-3 py-2 text-white"
          />
        </View>

        {/* BALANCE */}
        <View className="mb-4">
          <Text className="text-sm font-medium mb-1">
            Balance after txn (optional)
          </Text>
          <TextInput
            value={balance}
            onChangeText={setBalance}
            placeholder="eg. 58000.50"
            placeholderTextColor={"#707070ff"}
            keyboardType="decimal-pad"
            className="border border-gray-700 rounded-md px-3 py-2 text-white"
          />
          <Text className="text-xs text-gray-500 mt-1">
            Recommended for more accurate insights.
          </Text>
        </View>

        {/* DATE TIME */}
        {/* <View className="mb-4">
          <Text className="text-sm font-medium mb-1">Date & time</Text>
          <Pressable
            onPress={() => setShowDatePicker(true)}
            className="border border-gray-700 rounded-md px-3 py-2"
          >
            <Text className="text-gray-800">{date.toLocaleString()}</Text>
          </Pressable>
          {showDatePicker && (
            <DateTimePicker
              value={date}
              mode="datetime"
              onChange={onChangeDate}
            />
          )}
        </View> */}
        <View className="mb-4">
          <Text className="text-sm font-medium mb-1">Date & time</Text>

          {/* display combined value */}
          <Pressable
            onPress={() => setShowDatePicker(true)}
            className="border border-gray-700 rounded-md px-3 py-2 mb-2"
          >
            <Text className="text-white">{date.toLocaleString()}</Text>
          </Pressable>

          <View className="flex-row">
            <Pressable
              onPress={() => setShowDatePicker(true)}
              className="mr-2 px-3 py-2 rounded-md border border-gray-700"
            >
              <Text className="text-xs text-white">Change date</Text>
            </Pressable>
            <Pressable
              onPress={() => setShowTimePicker(true)}
              className="px-3 py-2 rounded-md border border-gray-700"
            >
              <Text className="text-xs text-white">Change time</Text>
            </Pressable>
          </View>

          {showDatePicker && (
            <DateTimePicker
              value={date}
              mode="date"
              display={Platform.OS === "ios" ? "spinner" : "default"}
              onChange={onChangeDate}
            />
          )}

          {showTimePicker && (
            <DateTimePicker
              value={date}
              mode="time"
              display={Platform.OS === "ios" ? "spinner" : "default"}
              onChange={onChangeTime}
            />
          )}
        </View>

        {/* COMMENT */}
        <View className="mb-6">
          <Text className="text-sm font-medium mb-1">
            Comment / note (optional)
          </Text>
          <TextInput
            value={comment}
            onChangeText={setComment}
            placeholder="e.g. Swiggy, office lunch, shared with X"
            placeholderTextColor={"#707070ff"}
            multiline
            numberOfLines={5}
            className="border border-gray-700 rounded-md px-3 py-2 text-sm text-white h-20"
            style={{ textAlignVertical: "top" }}
          />
        </View>

        <Pressable
          onPress={handleSubmit}
          disabled={loading}
          className={`rounded-md py-3 items-center ${
            loading ? "bg-emerald-300" : "bg-emerald-600"
          }`}
        >
          <Text className="text-white font-semibold">
            {loading ? "Saving..." : "Save transaction"}
          </Text>
        </Pressable>
      </ScrollView>

      {/* Consent promo modal */}
      <Modal
        visible={modalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setModalVisible(false)}
      >
        <View
          className="flex-1 justify-center items-center"
          style={{ backgroundColor: "rgba(10, 10, 10, 0.97)" }}
        >
          <View className="bg-white rounded-2xl px-6 py-5 w-11/12 border !border-blue-600">
            <Text className="text-lg font-semibold mb-2">
              Transaction added
            </Text>
            <Text className="text-sm text-gray-700 mb-3">
              Your manual entry is saved. We’ll use it to update your spending
              insights shortly.
            </Text>
            <Text className="text-sm text-gray-600 mb-4">
              Manually entering every transaction can be time-consuming. You can
              skip all this by giving consent once so we can fetch your
              transactions automatically.
            </Text>

            <Pressable
              onPress={() => {
                setModalVisible(false);
                // open your Setu consent flow here
                // e.g. router.push("/(auth)/consentScreen");
              }}
              className="bg-blue-600 rounded-md py-3 items-center mb-3"
            >
              <Text className="text-white font-semibold">
                Give consent & automate
              </Text>
            </Pressable>

            <Pressable
              onPress={() => setModalVisible(false)}
              className="py-2 items-center"
            >
              <Text className="text-sm text-gray-600">
                Continue adding manually
              </Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </PageView>
  );
}
