// app/(auth)/Chat.tsx
import { PageView, Text, View } from "@/components/Themed";
import { urls } from "@/constants/urls";
import request from "@/services/api/request";
import { useAuthStore } from "@/store/useAuthStore";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  TextInput,
  TouchableOpacity,
} from "react-native";

type ChatMessage = {
  id: string;
  text: string;
  role: "user" | "assistant";
  createdAt: string;
};

export default function ChatScreen() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isLoggedIn } = useAuthStore();
  const listRef = useRef<FlatList<ChatMessage>>(null);

  //   const fetchMessages = async () => {
  //     try {
  //       setLoading(true);
  //       setError(null);

  //       // backend can return DESC (latest first)
  //       const { data, HttpStatusCode, status } = await request<any>(
  //         "GET",
  //         urls.auth.chat_messages,
  //         {},
  //         {}
  //       );

  //       if (HttpStatusCode.OK === status && data.success) {
  //         const apiMessages: ChatMessage[] = data.data;

  //         // we reverse so UI is oldest at top, newest at bottom
  //         const ordered = apiMessages.slice().reverse();
  //         setMessages(ordered);
  //       }
  //     } catch (e: any) {
  //       setError(e.message || "failed to load messages");
  //     } finally {
  //       setLoading(false);
  //     }
  //   };

  //   useEffect(() => {
  //     if (isLoggedIn) fetchMessages();
  //   }, [isLoggedIn]);

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      listRef.current?.scrollToEnd({ animated: false });
    });
  };

  useEffect(() => {
    if (!loading) scrollToBottom();
  }, [messages.length, loading]);

  const handleSend = async () => {
    if (!input.trim() || sending) return;

    const text = input.trim();
    setInput("");
    // Keyboard.dismiss();

    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      text,
      role: "user",
      createdAt: new Date().toISOString(),
    };

    scrollToBottom();

    try {
      setSending(true);

      // later this will hit python agent API
        const { data, HttpStatusCode, status } = await request<any>(
          "POST",
          urls.auth.chat,
          {  },
          {message: text}
        );

        if (HttpStatusCode.OK === status && data.success) {
          setMessages((prev) => [...prev, tempUserMsg]);
          const reply: ChatMessage = data.data; // ensure backend returns same shape
          setMessages((prev) => [...prev, reply]);
          scrollToBottom();
        } else {
          throw new Error("send failed");
        }
    } catch (e: any) {
      setError(e.message || "failed to send");
    } finally {
      setSending(false);
    }
  };

  const renderItem = ({ item }: { item: ChatMessage }) => {
    const isUser = item.role === "user";

    return (
      <View
        className={`mb-2 px-2 ${!isUser ? "items-start" : "items-end"} mt-4`}
      >
        <View
          className={`max-w-[60%] rounded-2xl px-3 py-2 border ${
            isUser ? "!bg-[#0866FF]" : "!bg-[#2f95dc]"
          }`}
        >
          <Text className="text-white text-xs">{item.text}</Text>
        </View>
      </View>
    );
  };

  return (
    <PageView className="flex-1 bg-black">
      <View className="flex-1 px-3 pt-3">
        <View className="flex-row items-center mb-3">
          <TouchableOpacity
            onPress={() => router.back()}
            className="mr-3 pr-1 py-1"
            activeOpacity={0.7}
          >
            <Ionicons name="chevron-back" size={22} color="#e5e5e5" />
          </TouchableOpacity>
          <View className="flex-1">
            <Text className="text-white text-lg font-semibold">
              Chat with NuoBot
            </Text>
            <Text className="text-neutral-500 text-[11px]">
              Ask anything about your money. We&apos;ll answer with AI-powered
              insights.
            </Text>
          </View>
        </View>

        {loading ? (
          <View className="flex-1 items-center justify-center">
            <ActivityIndicator />
          </View>
        ) : (
          <>
            {error && (
              <View className="bg-red-900/40 rounded-xl px-3 py-2 mb-2">
                <Text className="text-red-300 text-[11px]">{error}</Text>
              </View>
            )}

            <FlatList
              ref={listRef}
              data={messages}
              keyExtractor={(item) => item.id}
              renderItem={renderItem}
              contentContainerStyle={{ paddingBottom: 12, paddingTop: 4 }}
              onContentSizeChange={scrollToBottom}
              showsVerticalScrollIndicator={false}
            />
          </>
        )}
      </View>

      {/* input bar */}
      <View className="px-3 pb-3 pt-1 bg-black">
        <View className="flex-row items-center bg-neutral-950 rounded-2xl px-3 py-2 border border-neutral-700">
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="Type a message..."
            placeholderTextColor="#6b7280"
            style={{
              flex: 1,
              color: "white",
              fontSize: 13,
              paddingVertical: 4,
            }}
            multiline
          />
          <TouchableOpacity
            onPress={handleSend}
            disabled={sending || !input.trim()}
            className={`ml-2 px-3 py-2 rounded-xl ${
              sending || !input.trim() ? "bg-neutral-700" : "bg-emerald-600"
            }`}
            activeOpacity={0.8}
          >
            <Text className="text-white text-xs font-semibold">
              {sending ? "..." : "Send"}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </PageView>
  );
}
