// app/(noauth)/login.tsx
import AppLogo from "@/assets/images/app-icon.png";
import AuthInput from "@/components/AuthInput";
import PasswordInput from "@/components/PasswordInput";
import { PageView, Text, View } from "@/components/Themed";
import Regex from "@/constants/Regex";
import { urls } from "@/constants/urls";
import request from "@/services/api/request";
import { useAuthStore, User } from "@/store/useAuthStore";
import { useRouter } from "expo-router";
import React, { useState } from "react";
import { Image, Pressable } from "react-native";
import Toast from "react-native-toast-message";

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const router = useRouter();

  const submit = async () => {
    if (!email.trim() || !password.trim()) {
      Toast.show({ type: "error", text1: "Please fill all fields" });
      return;
    }

    if (!Regex.email.test(email)) {
      Toast.show({ type: "error", text1: "Invalid email" });
      return;
    }

    setLoading(true);

    try {
      const { data, HttpStatusCode, status } = await request(
        "POST",
        urls.noauth.login,
        {},
        {
          email,
          password,
        }
      );

      if (data.success && status === HttpStatusCode.OK) {
        login(data.data as User);
        Toast.show({
          type: "success",
          text1: "Logged in",
        });
        router.replace("/(auth)/(tabs)/home");
      }
    } catch (error) {
      Toast.show({
        type: "error",
        text1: "Something went wrong",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageView className="flex-1 px-6 pt-12 mb-5 justify-center">
      <View className="items-center mb-8">
        <Image source={AppLogo} className="w-20 h-20 mb-4" />
        <Text className="text-2xl font-semibold mt-4 text-center">Welcome back</Text>
        <Text className="text-sm text-gray-500 mt-1">Sign in to continue</Text>
      </View>

      <View className="bg-white rounded-2xl px-5 py-6 shadow-sm space-y-5">
        <AuthInput
          label="Email"
          value={email}
          onChangeText={setEmail}
          placeholder="Enter your email"
          keyboardType="email-address"
        />

        <PasswordInput
          label="Password"
          value={password}
          onChangeText={setPassword}
          placeholder="********"
          show={showPass}
          onToggle={() => setShowPass((s) => !s)}
        />

        <Pressable
          onPress={submit}
          className={`rounded-md py-3 items-center ${loading ? "bg-blue-300" : "bg-blue-600"}`}
          android_ripple={{ color: "#0866ff" }}
          accessibilityRole="button"
          accessibilityState={{ busy: loading }}
        >
          <Text className={`text-white font-semibold ${loading ? "" : ""}`}>
            {loading ? "Logging in..." : "Login"}
          </Text>
        </Pressable>

        <Pressable
          onPress={() => router.push("/(noauth)/register")}
          className="items-center mt-4"
        >
          <Text className="text-sm !text-gray-400">
            Don't have an account? <Text className="underline">Register</Text>
          </Text>
        </Pressable>
      </View>

      {/* <View className="flex-1" />
      <View className="items-center pb-6">
        <Text className="text-xs text-gray-400">
          By continuing you agree to terms
        </Text>
      </View> */}
    </PageView>
  );
}
