import { withAuth } from "@/app/lib/middleware";
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib/prisma";

export async function GET(request: NextRequest) {
  return withAuth(request, async (req: any) => {
    try {
      const consent = await prisma.accountAggregatorConsent.findFirst({
        where: { userId: String(req.user.userId) },
        orderBy: { createdAt: "desc" },
        select: {
          id: true,
          consentId: true,
          status: true,
          consentStart: true,
          consentExpiry: true,
          createdAt: true,
          updatedAt: true,
          pan: true,
          url: true,
        },
      });

      if (!consent)
        return NextResponse.json(
          { success: true, data: null, message: "No consent found" },
          { status: 200 }
        );

      return NextResponse.json(
        {
          success: true,
          data: consent ?? null,
          message: "Consent details found",
        },
        { status: 200 }
      );
    } catch (error) {
      console.log("get my consent error:", error);
      return NextResponse.json(
        {
          success: false,
          data: null,
          message: "Failed to get consent details",
        },
        { status: 500 }
      );
    }
  });
}
