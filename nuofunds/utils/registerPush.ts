import { storageKeys } from "@/constants/storageKeys";
import { urls } from "@/constants/urls";
import request from "@/services/api/request";
// import Constants from "expo-constants";
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

// --------------
// 1) FOREGROUND HANDLER (top-level, runs once)
// --------------
Notifications.setNotificationHandler({
  handleNotification: async (notification) => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export async function getStoredPushToken(): Promise<string | null> {
  try {
    return (await SecureStore.getItemAsync(storageKeys.device_token)) || null;
  } catch {
    return null;
  }
}

export async function setStoredPushToken(token: string): Promise<void> {
  try {
    await SecureStore.setItemAsync(storageKeys.device_token, token);
  } catch (e) {
    console.warn("setStoredPushToken failed", e);
  }
}

function getDeviceType() {
  if (Platform.OS === "ios") return 1;
  if (Platform.OS === "android") return 2;
  return 0;
}

async function askNotificationPermission() {
  if (!Device.isDevice) return null;

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    console.log("Notification permission not granted");
    return null;
  }

  return finalStatus;
}

// --------------
// 2) LISTENER REGISTRATION (once)
// --------------
let listenersRegistered = false;
let removeListeners: (() => void) | null = null;

function registerNotificationListenersOnce() {
  if (listenersRegistered) return;

  console.log("🔔 registering notification listeners...");

  const receivedSub = Notifications.addNotificationReceivedListener((notif) => {
    console.log("🔔 [FOREGROUND NOTIF]", JSON.stringify(notif, null, 2));
  });

  const tappedSub = Notifications.addNotificationResponseReceivedListener((resp) => {
    console.log("📲 [NOTIF TAPPED]", JSON.stringify(resp, null, 2));
  });

  removeListeners = () => {
    receivedSub.remove();
    tappedSub.remove();
  };

  listenersRegistered = true;
}

// optional export for logout cleanup if you want later
export function cleanupNotificationListeners() {
  if (removeListeners) {
    removeListeners();
    removeListeners = null;
    listenersRegistered = false;
    console.log("🔕 notification listeners cleaned up");
  }
}


export async function syncPushTokenWithBackend(isLoggedIn: boolean) {
  if (!isLoggedIn) return;

  const perm = await askNotificationPermission();
  if (!perm) return;


  // ✅ only when user is logged in AND permission granted
  registerNotificationListenersOnce();

  // 👇 THIS is the important change: native push token (FCM on Android, APNs on iOS)
  const { data: newToken, type } =
    await Notifications.getDevicePushTokenAsync();
  console.log("device push token type:", type, "token:", newToken);

  if (!newToken) return;

  const storedToken = await getStoredPushToken();

  // if unchanged, do nothing
  if (storedToken && storedToken === newToken) {
    return;
  }

  const deviceType = getDeviceType();

  // 1) if there was an old token, clear it on backend FIRST
  if (storedToken && storedToken !== newToken) {
    try {
      const { data, status, HttpStatusCode } = await request(
        "DELETE",
        urls.auth.notification.manage_token,
        {},
        {
          token: storedToken, // 👈 delete OLD token, not new one
        }
      );

      if (status === HttpStatusCode.OK && data.success) {
        console.log("Old push token cleared from backend");
      } else {
        console.warn("Failed to clear old push token on backend");
      }
    } catch (e) {
      console.warn("Error clearing old push token", e);
    }
  }

  // 2) register the new token with backend
  try {
    const { data, status, HttpStatusCode } = await request(
      "POST",
      urls.auth.notification.manage_token,
      {},
      {
        device_type: deviceType,
        token: newToken,
      }
    );

    if (status === HttpStatusCode.CREATED && data.success) {
      console.log("Push token synced with backend");
      await setStoredPushToken(newToken);
    } else {
      console.warn("Failed to sync push token with backend");
    }
  } catch (e) {
    console.warn("Error syncing push token", e);
  }
}
