// app/(noauth)/register.tsx
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


export default function RegisterScreen() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const router = useRouter();

  const submit = async () => {
    if (!email.trim() || !name.trim() || !password.trim() || !phone.trim()) {
      Toast.show({ type: "error", text1: "Please fill all fields" });
      return;
    }
      
    if (!Regex.email.test(email)) {
      Toast.show({ type: "error", text1: "Invalid email" });
      return;
    }

    if (phone.trim().length !== 10) {
      Toast.show({ type: "error", text1: "Invalid phone" });
      return;
    }

    if (!Regex.password.test(password)) {
      Toast.show({ type: "error", text1: "Password must be at least 8 characters long and contain at least one uppercase, lowercase, number, and special character" });
      return;
    }

    if (password.trim() !== confirmPassword.trim()) {
      Toast.show({ type: "error", text1: "Passwords do not match" });
      return;
    }

    setLoading(true);

    try {
      const { data, HttpStatusCode, status } = await request(
        "POST",
        urls.noauth.register,
        {},
        {
          email,
          password,
          name,
          phone,
        }
      );

      if (data.success && status === HttpStatusCode.CREATED) {
        login(data.data as User);
        Toast.show({
          type: "success",
          text1: "User registered",
        });
        setTimeout(() => {
          router.replace("/(auth)/consentScreen");
        }, 1000);
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
    <PageView className="flex-1 px-6 pt-12 justify-center">
      <View className="items-center mb-8">
        <Image source={AppLogo} className="w-20 h-20 mb-4" />
        <Text className="text-2xl font-semibold mt-4">Create account</Text>
        {/* <Text className="text-sm text-gray-500 mt-1">Quick sign up</Text> */}
      </View>

      <View className="bg-white rounded-2xl px-5 py-6 shadow-sm">
        <AuthInput
          label="Name"
          value={name}
          onChangeText={setName}
          placeholder="Enter your name"
        />
        <AuthInput
          label="Email"
          value={email}
          onChangeText={setEmail}
          placeholder="Enter your email"
          keyboardType="email-address"
        />

        <AuthInput
          label="Phone"
          value={phone}
          onChangeText={setPhone}
          placeholder="Enter your phone number"
          keyboardType="phone-pad"
        />

        <PasswordInput
          label="Password"
          value={password}
          onChangeText={setPassword}
          placeholder="Enter a password"
          show={showPass}
          onToggle={() => setShowPass((s) => !s)}
        />

        <PasswordInput
          label="Confirm password"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          placeholder="Confirm password"
          show={showConfirm}
          onToggle={() => setShowConfirm((s) => !s)}
        />

        <Pressable
          onPress={submit}
          className={`rounded-md py-3 items-center ${loading ? "!bg-blue-600" : "!bg-[#0866ff]"}`}
          android_ripple={{ color: "#133b92ff" }}
          accessibilityRole="button"
          accessibilityState={{ busy: loading }}
        >
          <Text className="text-white font-semibold">
            {loading ? "Registering..." : "Register"}
          </Text>
        </Pressable>

        <Pressable
          onPress={() => router.push("/(noauth)/login")}
          className="items-center mt-4"
        >
          <Text className="text-sm !text-gray-400">
            Already have an account? <Text className="underline">Login</Text>
          </Text>
        </Pressable>
      </View>

    </PageView>
  );
}
