import { removeAuthFromStorage, syncAuthToStorage } from "@/utils/auth";
import { create } from "zustand";

export type User = {
  id: string;
  name: string;
  email: string;
  phone: string;
  consent: boolean;
  token: string;
} | null;

export type AuthState = {
  user: User;
  token: string | null;
  isLoggedIn: boolean;
  consentGiven: boolean;
  login: (user: User) => void;
  logout: () => void;
  setConsent: (v: boolean) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoggedIn: false,
  consentGiven: false,
  login: (user) => {
    set({ user, isLoggedIn: true, consentGiven: user?.consent ?? false, token: user?.token ?? null });
    syncAuthToStorage('user_data', user);
    syncAuthToStorage('token', user?.token);
  },
  logout: () => {
    set({ user: null, isLoggedIn: false, consentGiven: false })
    removeAuthFromStorage();
  },
  setConsent: (v: boolean) => set({ consentGiven: v }),
}));
