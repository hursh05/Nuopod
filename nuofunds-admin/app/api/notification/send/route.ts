import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib//prisma";
import { withAuth } from "@/app/lib/middleware";
import { fcm } from "@/app/firebase";

export async function POST(req: NextRequest) {
  return withAuth(req, async (req: any) => {
    try {
      const { title, messageBody, extraData } = await req.json();

      // fetch all devices for this user
      const devices = await prisma.deviceTokens.findMany({
        where: { userId: req.user.userId },
        select: { id: true, token: true, deviceType: true },
      });

      if (!devices.length) {
        return NextResponse.json(
          { success: false, message: "No devices found" },
          { status: 400 }
        );
      }

      // const devices = [
      //   {
      //     id: 'dsd55eeeecc',
      //     token: 'eydasdaddsada3ffafdfafdfa515dadasdasda34232fffdfsffsaf',
      //     deviceType: 1
      //   }
      // ]

      const results = await Promise.all(
        devices.map(async (d) => {
          const msg = {
            token: d.token,
            notification: {
              title,
              body: messageBody,
            },
            data: {
              ...extraData,
              userId: String(req.user.userId),
              deviceType: String(d.deviceType),
            },
          };

          try {
            const resp = await fcm.send(msg);
            return { token: d.token, ok: true, resp };
          } catch (err) {
            console.error("FCM send error for token", d.token, err);
            return { token: d.token, ok: false, error: String(err) };
          }
        })
      );

      const successCount = results.filter((r) => r.ok).length;
      const failureCount = results.length - successCount;

      return NextResponse.json(
        {
          success: true,
          message: "message sent successfully",
          successCount,
          failureCount,
          results,
        },
        { status: 200 }
      );
    } catch (error) {
      console.log("push/send error", error);
      return NextResponse.json({ error: "server error" }, { status: 500 });
    }
  });
}
