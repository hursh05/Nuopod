import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib//prisma";
import { withAuth } from "@/app/lib/middleware";

type HomeResponse = {
  dailySummary: {
    date: string;
    totalIncome: number;
    totalExpense: number;
    netAmount: number;
    closingBalance: number | null;
  } | null;
  forecastSummary: {
    fromDate: string;
    toDate: string;
    predictedIncome: number;
    predictedExpense: number;
    predictedShortfall: number;
    highestRiskDay: {
      date: string;
      riskLevel: string;
    } | null;
  } | null;
  expenseSummary: {
    period: "30d";
    totalExpense: number;
    topCategories: {
      category: string;
      amount: number;
      percent: number;
    }[];
  } | null;
  actionCards: {
    id: string;
    title: string;
    message: string;
    priority: string;
    category: string | null;
    expectedSavings: number | null;
    daysUntilImpact: number | null;
  }[];
  streakSummary: {
    totalActiveStreaks: number;
    topStreak?: {
      streakType: string;
      currentStreak: number;
      longestStreak: number;
      nextMilestone: number | null;
    };
  } | null;
  financialInsights: {
    analysisDate: string | null;
    analysisPeriodDays: number;
    avgDailyIncome: number;
    avgDailyExpense: number;
    savingsRate: number;
    totalSavingsLast30Days: number;
    financialHealthGrade: string | null;
    overallRiskLevel: string | null;
    insightsSummary: string | null;
  } | null;
};

export async function GET(req: NextRequest) {
  return withAuth(req, async (req: any) => {
    try {
      const userId = req.user.userId;

      if (!userId) {
        return NextResponse.json(
          { error: "userId is required" },
          { status: 400 }
        );
      }

      const today = new Date();
      //   today.setHours(0, 0, 0, 0);

      const d30 = new Date();
      d30.setDate(today.getDate() - 30);

      const d7 = new Date();
      d7.setDate(today.getDate() + 7);

      // 1) latest DailyFeatures row (today-ish)
      const latestDaily = await prisma.dailyFeatures.findFirst({
        where: { userId, date: today },
      });

      const dailySummary: HomeResponse["dailySummary"] = latestDaily
        ? {
            date: latestDaily.date.toISOString(),
            totalIncome: Number(latestDaily.totalIncome ?? 0),
            totalExpense: Number(latestDaily.totalExpense ?? 0),
            netAmount: Number(latestDaily.netAmount ?? 0),
            closingBalance: latestDaily.closingBalance
              ? Number(latestDaily.closingBalance)
              : null,
          }
        : null;

      // 2) forecast for next 7 days
      const incomeForecast = await prisma.incomeForecast.findMany({
        where: {
          userId,
          forecastDate: {
            gte: today,
            lte: d7,
          },
        },
      });

      const expenseForecast = await prisma.expenseForecast.findMany({
        where: {
          userId,
          forecastDate: {
            gte: today,
            lte: d7,
          },
        },
      });

      const shortfalls = await prisma.shortfall.findMany({
        where: {
          userId,
          forecastDate: {
            gte: today,
            lte: d7,
          },
        },
      });

      let predictedIncome = 0;
      let predictedExpense = 0;
      let predictedShortfall = 0;
      let highestRiskDay: { date: string; riskLevel: string } | null = null;

      incomeForecast.forEach((f) => {
        predictedIncome += Number(f.predictedIncome);
      });
      expenseForecast.forEach((f) => {
        predictedExpense += Number(f.predictedExpense);
      });
      shortfalls.forEach((s) => {
        predictedShortfall += Number(s.predictedShortfall);
        if (!highestRiskDay || s.riskLevel > highestRiskDay.riskLevel) {
          highestRiskDay = {
            date: s.forecastDate.toISOString(),
            riskLevel: s.riskLevel,
          };
        }
      });

      const forecastSummary: HomeResponse["forecastSummary"] =
        incomeForecast.length || expenseForecast.length || shortfalls.length
          ? {
              fromDate: today.toISOString(),
              toDate: d7.toISOString(),
              predictedIncome,
              predictedExpense,
              predictedShortfall,
              highestRiskDay,
            }
          : null;

      // 3) expense classification summary for last 30 days
      const classifiedTx = await prisma.transactionClassification.findMany({
        where: { userId },
        include: {
          Transaction: {
            select: {
              amount: true,
              date: true,
            },
          },
        },
      });

      const expenseByCategory: Record<string, number> = {};
      let totalExpense = 0;

      classifiedTx.forEach((tc) => {
        if (!tc.Transaction) return;
        const txDate = tc.Transaction.date;
        if (txDate < d30 || txDate > today) return;
        if (tc.isIncome) return; // only expenses

        const amt = Number(tc.Transaction.amount ?? 0);
        totalExpense += amt;
        const cat = tc.category || "Other";
        expenseByCategory[cat] = (expenseByCategory[cat] || 0) + amt;
      });

      const topCategories = Object.entries(expenseByCategory)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([category, amount]) => ({
          category,
          amount,
          percent: totalExpense ? (amount / totalExpense) * 100 : 0,
        }));

      const expenseSummary: HomeResponse["expenseSummary"] =
        totalExpense > 0
          ? {
              period: "30d",
              totalExpense,
              topCategories,
            }
          : null;

      // 4) action cards (pending)
      const actionCardsRaw = await prisma.actionCard.findMany({
        where: {
          userId,
          status: "pending",
        },
        orderBy: [
          { isUrgent: "desc" },
          { priority: "desc" },
          { createdAt: "desc" },
        ],
        take: 3,
      });

      const actionCards: HomeResponse["actionCards"] = actionCardsRaw.map(
        (c) => ({
          id: c.id,
          title: c.title,
          message: c.message,
          priority: c.priority,
          category: c.category,
          expectedSavings: c.expectedSavings ? Number(c.expectedSavings) : null,
          daysUntilImpact: c.daysUntilImpact ?? null,
        })
      );

      // 5) streak summary
      const streaks = await prisma.motivationStreak.findMany({
        where: {
          userId,
          isActive: true,
        },
      });

      let topStreak:
        | {
            streakType: string;
            currentStreak: number;
            longestStreak: number;
            nextMilestone: number | null;
          }
        | undefined;

      if (streaks.length) {
        const savings = streaks.find((s) => s.streakType === "savings");
        const best =
          savings ||
          streaks.sort(
            (a, b) => (b.currentStreak ?? 0) - (a.currentStreak ?? 0)
          )[0];

        topStreak = {
          streakType: best.streakType,
          currentStreak: best.currentStreak ?? 0,
          longestStreak: best.longestStreak ?? 0,
          nextMilestone: best.nextMilestone ?? null,
        };
      }

      const streakSummary: HomeResponse["streakSummary"] = streaks.length
        ? {
            totalActiveStreaks: streaks.length,
            topStreak,
          }
        : null;

      // 6) financial insights (latest analysis)
      const latestInsights = await prisma.userFinancialInsights.findFirst({
        where: { userId },
        orderBy: { analysisDate: "desc" },
      });

      const financialInsights: HomeResponse["financialInsights"] =
        latestInsights
          ? {
              analysisDate: latestInsights.analysisDate
                ? latestInsights.analysisDate.toISOString()
                : null,
              analysisPeriodDays: latestInsights.analysisPeriodDays ?? 30,
              avgDailyIncome: Number(latestInsights.avgDailyIncome ?? 0),
              avgDailyExpense: Number(latestInsights.avgDailyExpense ?? 0),
              savingsRate: Number(latestInsights.savingsRate ?? 0),
              totalSavingsLast30Days: Number(
                latestInsights.totalSavingsLast30Days ?? 0
              ),
              financialHealthGrade: latestInsights.financialHealthGrade ?? null,
              overallRiskLevel: latestInsights.overallRiskLevel ?? null,
              insightsSummary: latestInsights.insightsSummary ?? null,
            }
          : null;

      const res: HomeResponse = {
        dailySummary,
        forecastSummary,
        expenseSummary,
        actionCards,
        streakSummary,
        financialInsights
      };

      return NextResponse.json(
        {
          success: true,
          data: res,
          message: "Dashboard data fetched successfully",
        },
        { status: 200 }
      );
    } catch (err) {
      console.log("home api error", err);
      return NextResponse.json({ error: "internal error" }, { status: 500 });
    }
  });
}
