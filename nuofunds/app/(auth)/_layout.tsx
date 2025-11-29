import { FloatingChatButton } from "@/components/FloatingChatButton";
import { Slot } from "expo-router";

export default function AuthRoot() {
  return (
    <>
      <Slot />
      <FloatingChatButton />
    </>
  );
}
