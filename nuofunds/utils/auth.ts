// utils/authStorage.ts (or overwrite your current file)
import { storageKeys } from "@/constants/storageKeys";
import { AuthState, User } from "@/store/useAuthStore";
import * as SecureStore from "expo-secure-store";

/**
 * Read stored auth and call login(user) if user exists
 */
const checkStoredAuth = async (login: AuthState["login"]) => {
  try {
    const tokenRaw = await SecureStore.getItemAsync(storageKeys.token);
    const userRaw = await SecureStore.getItemAsync(storageKeys.user_data);

    const token = tokenRaw ? JSON.parse(tokenRaw) : null;
    const userData = userRaw ? (JSON.parse(userRaw) as User) : null;

    if (userData) {
      login(userData);
    }

    // return { token, user: userData };
  } catch (e) {
    console.warn("checkStoredAuth failed", e);
    return { token: null, user: null };
  }
};

/**
 * Sync token or user_data to secure store
 */
const syncAuthToStorage = async (type: "token" | "user_data", data: User | any) => {
  try {
    const key = type === "token" ? storageKeys.token : storageKeys.user_data;
    const payload = typeof data === "string" ? data : JSON.stringify(data);
    await SecureStore.setItemAsync(key, payload);
    return true;
  } catch (e) {
    console.warn("syncAuthToStorage failed", e);
    return false;
  }
};

/**
 * Remove both token and user_data from secure store
 */
const removeAuthFromStorage = async () => {
  try {
    await SecureStore.deleteItemAsync(storageKeys.token);
    await SecureStore.deleteItemAsync(storageKeys.user_data);
    await SecureStore.deleteItemAsync(storageKeys.device_token);
    return true;
  } catch (e) {
    console.warn("removeAuthFromStorage failed", e);
    return false;
  }
};

export { checkStoredAuth, removeAuthFromStorage, syncAuthToStorage };
