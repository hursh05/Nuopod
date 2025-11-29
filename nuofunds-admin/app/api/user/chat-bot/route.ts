import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib/prisma";
import { withAuth } from "@/app/lib/middleware";
import axios from "axios";

export async function POST(req: NextRequest) {
  return withAuth(req, async (req: any) => {
    try {
      const { message } = await req.json();

      if (!message) {
        return NextResponse.json(
          { success: false, message: "message required" },
          { status: 400 }
        );
      }

      const res = await axios.post(
        "http://127.0.0.1:5000/chat",
        {
          user_id: req.user.userId,
          message: message,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const data = {
        id: `temp-${Date.now()}`,
        text: res.data.response,
        role: "assistant",
        createdAt: new Date().toISOString(),
      };

      return NextResponse.json(
        { success: true, data: data },
        { status: 200 }
      );
    } catch (error) {
      console.log("chat-bot error", error);
      return NextResponse.json({ success: false, error: "server error" }, { status: 500 });
    }
  });
}
