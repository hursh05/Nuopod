import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib/prisma";
import { withAuth } from "@/app/lib/middleware";

export async function GET(req: NextRequest) {
  return withAuth(req, async (req: any) => {
    try {
      const userId = req.user.userId;

      if (!userId) {
        return NextResponse.json(
          { success: false, message: "User ID missing" },
          { status: 400 }
        );
      }

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const futureDate = new Date(today);
      futureDate.setDate(today.getDate() + 7);

      const [incomeRows, expenseRows, shortfallRows] = await Promise.all([
        prisma.incomeForecast.findMany({
          where: { userId, forecastDate: { gte: today, lte: futureDate } },
          orderBy: { forecastDate: "asc" },
        }),
        prisma.expenseForecast.findMany({
          where: { userId, forecastDate: { gte: today, lte: futureDate } },
          orderBy: { forecastDate: "asc" },
        }),
        prisma.shortfall.findMany({
          where: { userId, forecastDate: { gte: today, lte: futureDate } },
          orderBy: { forecastDate: "asc" },
        }),
      ]);

      const merged: any[] = [];

      for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);

        const iso = date.toISOString().split("T")[0];

        const inc = incomeRows.find(
          (x) => x.forecastDate.toISOString().startsWith(iso)
        );
        const exp = expenseRows.find(
          (x) => x.forecastDate.toISOString().startsWith(iso)
        );
        const sf = shortfallRows.find(
          (x) => x.forecastDate.toISOString().startsWith(iso)
        );

        merged.push({
          date: date.toISOString(),
          predictedIncome: inc ? Number(inc.predictedIncome) : 0,
          predictedExpense: exp ? Number(exp.predictedExpense) : 0,
          predictedShortfall: sf ? Number(sf.predictedShortfall) : 0,
          riskLevel: sf ? sf.riskLevel : "LOW",
        });
      }

      return NextResponse.json(
        {
          success: true,
          data: {
            days: merged.length,
            entries: merged,
          },
        },
        { status: 200 }
      );
    } catch (e) {
      console.log("forecast-details error", e);
      return NextResponse.json(
        { success: false, message: "Internal error" },
        { status: 500 }
      );
    }
  });
}
