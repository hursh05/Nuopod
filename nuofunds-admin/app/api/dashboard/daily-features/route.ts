import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib/prisma";
import { withAuth } from "@/app/lib/middleware";

export async function GET(req: NextRequest) {
  return withAuth(req, async (req: any) => {
    try {
      const { searchParams } = new URL(req.url);
      const userId = req.user.userId;
      const daysParam = searchParams.get("days");
      // this is now "max records", not date window
      const limit = daysParam ? parseInt(daysParam, 10) : 30;

      if (!userId) {
        return NextResponse.json(
          { error: "userId is required" },
          { status: 400 }
        );
      }

      // get latest N rows by date
      const rowsDesc = await prisma.dailyFeatures.findMany({
        where: { userId },
        orderBy: { date: "desc" },
        take: limit,
      });

      // reverse to ascending for charts
      const rows = rowsDesc.reverse();

      const result = {
        // actual count (maybe < limit if not enough data)
        days: rows.length,
        points: rows.map((r) => ({
          date: r.date.toISOString(),
          totalIncome: Number(r.totalIncome ?? 0),
          totalExpense: Number(r.totalExpense ?? 0),
          netAmount: Number(r.netAmount ?? 0),
          closingBalance: r.closingBalance
            ? Number(r.closingBalance)
            : null,
          transactionCount: r.transactionCount ?? 0,
        })),
      };

      return NextResponse.json(
        {
          success: true,
          data: result,
          message: "Daily features fetched successfully",
        },
        { status: 200 }
      );
    } catch (err) {
      console.log("daily-features api error", err);
      return NextResponse.json(
        { error: "internal error" },
        { status: 500 }
      );
    }
  });
}
