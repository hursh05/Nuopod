// app/(auth)/consent.tsx
import { PageView, Text, View } from "@/components/Themed";
import { urls } from "@/constants/urls";
import request from "@/services/api/request";
import { useAuthStore } from "@/store/useAuthStore";
import * as Linking from "expo-linking";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import React, { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView } from "react-native";
import Toast from "react-native-toast-message";

export default function ConsentScreen() {
  const router = useRouter();
  const { setConsent, token, user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [consentData, setConsentData] = useState<any>(null);
  const [fetchError, setFetchError] = useState(null);

  const params = useLocalSearchParams();

  const [success, setSuccess] = useState<any>(null);
  const [consentId, setConsentId] = useState<any>(null);
  const [errorcode, setErrorcode] = useState<any>(null);
  const [errormsg, setErrormsg] = useState<any>(null);

  useEffect(() => {
    setSuccess(params.success ?? null);
    setConsentId(params.consentId ?? params.id ?? null);
    setErrorcode(params.errorcode ?? null);
    setErrormsg(params.errormsg ?? null);
  }, [params]);

  async function fetchConsent() {
    setLoading(true);
    setFetchError(null);
    try {
      const { data, status, HttpStatusCode } = await request<any>(
        "GET",
        urls.auth.getConsent,
        {},
        {}
      );

      console.log("data >>", data);

      if (data.success && status === HttpStatusCode.OK) {
        setConsentData(data.data);
      }
    } catch (e) {
      // setFetchError(String(e));
      setConsentData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (Boolean(success) === true) {
      setConsent(true);
    }
    fetchConsent();
  }, [success, consentId]);

  const onSkip = () => {
    setConsent(false);
    Toast.show({
      type: "info",
      text1: "Skipped",
      text2: "You can review later.",
    });
    // land straight in tabs
    router.replace("/(auth)/(tabs)/home");
  };

  const onGiveConsent = async () => {
    setLoading(true);
    try {
      const { data, status, HttpStatusCode } = await request<any>(
        "GET",
        urls.auth.consent,
        {},
        {}
      );

      if (data.success && status === HttpStatusCode.OK) {
        const redirectUrl = Linking.createURL("consentScreen");

        const result = await WebBrowser.openAuthSessionAsync(
          data?.data?.url, // setu start url
          redirectUrl // MUST match env (expo go vs real app)
        );
      }
    } catch (err) {
      Toast.show({
        type: "error",
        text1: "Failed",
        text2: "Could not open browser",
      });
    } finally {
      setLoading(false);
    }
  };

  function ConsentCard({ c }: any) {
    if (!c) return null;
    // const isActive = c.status === "ACTIVE";
    return (
      <View className="bg-white rounded-2xl px-5 py-6 shadow-sm">
        <View className="mt-2 space-y-2">
          {/* <Row label="Consent ID" value={c.consentId} /> */}
          <Row label="Status" value={c.status} />
          <Row
            label="Start"
            value={
              c.consentStart ? new Date(c.consentStart).toLocaleString() : "-"
            }
          />
          <Row
            label="Expiry"
            value={
              c.consentExpiry ? new Date(c.consentExpiry).toLocaleString() : "-"
            }
          />
          {/* <Row label="PAN" value={c.pan ?? "-"} /> */}
        </View>

        <Pressable
          onPress={() => {
            router.replace("/(auth)/(tabs)/home");
          }}
          className={`rounded-md py-3 items-center mt-4 ${loading ? "bg-gray-400" : "bg-white"}`}
          android_ripple={{ color: "#2563eb" }}
        >
          <Text className="!text-black font-semibold">
            {loading ? "Loading..." : "Go to home"}
          </Text>
        </Pressable>
      </View>
    );
  }

  function Row({ label, value }: any) {
    return (
      <View className="flex-row justify-between items-center py-2 border-b border-gray-500">
        <Text className="text-sm text-gray-500">{label}</Text>
        <Text className="text-sm text-gray-700">{value}</Text>
      </View>
    );
  }

  return (
    // <PageView className="flex-1 bg-gray-50 px-6 pt-12 ">
    //   <View className="items-center mb-8">
    //     <View className="w-20 h-20 rounded-lg bg-gray-200 items-center justify-center">
    //       <Text className="text-lg font-bold text-gray-500">LOGO</Text>
    //     </View>
    //     <Text className="text-xl font-semibold mt-4">A few quick steps</Text>
    //     <Text className="text-sm text-gray-500 mt-1 text-center">
    //       We need your consent to continue. You can read details before giving
    //       consent.
    //     </Text>
    //   </View>

    //   <View className="bg-white rounded-2xl px-5 py-6 shadow-sm">
    //     <Text className="text-base font-medium mb-3">Consent</Text>
    //     <Text className="text-sm text-gray-600 mb-4">
    //       By giving consent you agree to our terms and privacy policy. Tap Give
    //       Consent to read the full document.
    //     </Text>

    //     {/* <Pressable
    //       onPress={onGiveConsent}
    //       className={`rounded-md py-3 items-center mb-3 ${loading ? "bg-blue-300" : "bg-blue-600"}`}
    //       android_ripple={{ color: "#2563eb" }}
    //     >
    //       <Text className="text-white font-semibold">{loading ? "Opening..." : "Give Consent"}</Text>
    //     </Pressable>

    //     <Pressable
    //       onPress={onSkip}
    //       className="rounded-md py-3 items-center border border-gray-200"
    //       android_ripple={{ color: "#e5e7eb" }}
    //     >
    //       <Text className="text-gray-700 font-medium">Skip for now</Text>
    //     </Pressable> */}

    //     {success === "true" ? (
    //       <View>
    //         <Text>Success: {success}</Text>
    //         <Text>Consent ID: {consentId}</Text>
    //       </View>
    //     ) : (
    //       <>
    //         {errormsg && (
    //           <View className="mb-4 p-3 bg-red-50 rounded-md border border-red-200">
    //             <Text className="text-red-600">{errormsg}</Text>
    //             {errorcode && (
    //               <Text className="text-red-500 text-sm mt-1">
    //                 Error Code: {errorcode}
    //               </Text>
    //             )}
    //           </View>
    //         )}

    //         <Pressable
    //           onPress={onGiveConsent}
    //           className={`rounded-md py-3 items-center mb-3 ${loading ? "bg-blue-300" : "bg-blue-600"}`}
    //           android_ripple={{ color: "#2563eb" }}
    //         >
    //           <Text className="text-white font-semibold">
    //             {loading ? "Opening..." : "Give Consent"}
    //           </Text>
    //         </Pressable>

    //         <Pressable
    //           onPress={onSkip}
    //           className="rounded-md py-3 items-center border border-gray-200"
    //           android_ripple={{ color: "#e5e7eb" }}
    //         >
    //           <Text className="text-gray-700 font-medium">Skip for now</Text>
    //         </Pressable>
    //       </>
    //     )}
    //   </View>

    //   <View className="flex-1" />
    //   <View className="items-center pb-6">
    //     <Text className="text-xs text-gray-400">
    //       You can change consent in settings later.
    //     </Text>
    //   </View>
    // </PageView>
    <PageView className="flex-1 px-2 pt-12">
      <ScrollView className="flex-1  pt-4">
        <View className="items-center mb-8 w-full">
          {
            consentData ? <Text className="!text-green-500 uppercase text-3xl font-bold">Granted!</Text>: <Text className="!text-red-500 uppercase text-3xl font-bold">Give Consent!</Text>
          }
        </View>

        {/* If success and consent fetched, show consent card; otherwise show CTA card */}
        {loading ? (
          <View className="bg-white rounded-2xl px-5 py-6 shadow-sm items-center">
            <ActivityIndicator size="large" />
          </View>
        ) : consentData ? (
          <ConsentCard c={consentData} />
        ) : (
          <View className="bg-white rounded-2xl px-5 py-6 shadow-sm">
            {errormsg && (
              <View className="mb-4 p-3 bg-red-50 rounded-md border border-red-200">
                <Text className="text-red-600">{errormsg}</Text>
                {errorcode && (
                  <Text className="text-red-500 text-sm mt-1">
                    Error Code: {errorcode}
                  </Text>
                )}
              </View>
            )}

            <Text className="text-xl font-semibold mt-4">
              A few quick steps
            </Text>
            <Text className="text-sm text-gray-500 mt-1 text-center">
              We need your consent to continue. You can read details before
              giving consent.
            </Text>

            <Text className="text-base font-medium mb-3">Consent</Text>
            <Text className="text-sm text-gray-600 mb-4">
              By giving consent you agree to our terms and privacy policy. Tap
              Give Consent to read the full document.
            </Text>

            <Pressable
              onPress={onGiveConsent}
              className={`rounded-md py-3 items-center mb-3 ${loading ? "bg-blue-300" : "bg-blue-600"}`}
              android_ripple={{ color: "#2563eb" }}
            >
              <Text className="text-white font-semibold">
                {loading ? "Opening..." : "Give Consent"}
              </Text>
            </Pressable>

            <Pressable
              onPress={onSkip}
              className="rounded-md py-3 items-center border border-gray-200"
              android_ripple={{ color: "#e5e7eb" }}
            >
              <Text className="text-gray-700 font-medium">Skip for now</Text>
            </Pressable>

            <Text className="text-sm text-gray-500 text-left mt-4">
              Don’t want to give consent?{" "}
              <Text
                className="!text-blue-600 underline"
                onPress={() => router.push("/(auth)/manual-transaction")}
              >
                add and manage your transactions manually
              </Text>
            </Text>
          </View>
        )}

        <View className="flex-1" />

        {/* small footer text stays at bottom (you asked to keep it) */}
        {
          !loading && !consentData && <View className="items-center pb-6">
          <Text className="text-xs text-gray-400 text-center px-6">
            By giving your consent you agree that we may access your financial
            data for the purposes described. You can change consent in settings
            later.
          </Text>
        </View>
        }
      </ScrollView>
    </PageView>
  );
}
