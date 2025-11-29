import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib/prisma";
import { withAuth } from "@/app/lib/middleware";
import { v4 as uuidv4 } from 'uuid';

export async function POST(req: NextRequest) {
  return withAuth(req, async (req: any) => {
    try {
      const { token, device_type } = await req.json();

      if (!token || !device_type) {
        return NextResponse.json(
          { success: false, message: "token and deviceType required" },
          { status: 400 }
        );
      }

      await prisma.deviceTokens.deleteMany({
        where: {
          userId: req.user.userId,
          deviceType: Number(device_type),
        },
      });

      // store new token
      await prisma.deviceTokens.create({
        data: {
          id: uuidv4(),
          token,
          userId: req.user.userId,
          deviceType: Number(device_type),
        },
      });

      return NextResponse.json(
        { success: true, message: "token registered successfully" },
        { status: 201 }
      );
    } catch (error) {
      console.log("push/register error", error);
      return NextResponse.json({ error: "server error" }, { status: 500 });
    }
  });
}

export async function DELETE(req: NextRequest) {
  return withAuth(req, async (req: any) => {
    try {
      const { token } = await req.json();

      if (!token) {
        return NextResponse.json({ success: false, message: "token required" }, { status: 400 });
      }

      await prisma.deviceTokens.deleteMany({
        where: { userId: req.user.userId, token },
      });

      return NextResponse.json(
        { success: true, message: "token deleted successfully" },
        { status: 200 }
      );
    } catch (error) {
        console.log("push/delete error", error);
        return NextResponse.json({ error: "server error" }, { status: 500 });
    }
  });
}
