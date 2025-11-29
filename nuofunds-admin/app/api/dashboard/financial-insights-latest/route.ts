import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib/prisma";
import { withAuth } from "@/app/lib/middleware";

export async function GET(req: NextRequest) {
  return withAuth(req, async (req: any) => {
    try {
      const userId = req.user.userId;

      if (!userId) {
        return NextResponse.json(
          { success: false, message: "User not found" },
          { status: 400 }
        );
      }

      const record = await prisma.userFinancialInsights.findFirst({
        where: { userId },
        orderBy: { analysisDate: "desc" },
      });

      if (!record) {
        return NextResponse.json(
          { success: true, data: null },
          { status: 200 }
        );
      }

      const data = {
        id: record.id,
        analysisDate: record.analysisDate?.toISOString() ?? null,
        analysisPeriodDays: record.analysisPeriodDays ?? 30,
        avgDailyIncome: Number(record.avgDailyIncome ?? 0),
        avgDailyExpense: Number(record.avgDailyExpense ?? 0),
        avgDailySavings: Number(record.avgDailySavings ?? 0),
        savingsRate: Number(record.savingsRate ?? 0),
        totalSavingsLast30Days: Number(record.totalSavingsLast30Days ?? 0),
        incomeStability: record.incomeStability,
        incomeStabilityScore: Number(record.incomeStabilityScore ?? 0),
        expenseStability: record.expenseStability,
        topExpenseCategory: record.topExpenseCategory,
        topExpenseCategoryAmount: Number(record.topExpenseCategoryAmount ?? 0),
        topExpenseCategoryPercent: Number(
          record.topExpenseCategoryPercent ?? 0
        ),
        unnecessarySpendingAmount: Number(record.unnecessarySpendingAmount ?? 0),
        avgDailyBalance: Number(record.avgDailyBalance ?? 0),
        lowestBalance: Number(record.lowestBalance ?? 0),
        lowestBalanceDate: record.lowestBalanceDate?.toISOString() ?? null,
        daysWithNegativeCashflow: record.daysWithNegativeCashflow ?? 0,
        daysWithLowBalance: record.daysWithLowBalance ?? 0,
        cashCrunchRisk: record.cashCrunchRisk,
        impulsivePurchases: record.impulsivePurchases ?? 0,
        spendingPatternType: record.spendingPatternType,
        averageTransactionSize: Number(record.averageTransactionSize ?? 0),
        highValueTransactions: record.highValueTransactions ?? 0,
        overallRiskLevel: record.overallRiskLevel,
        riskScore: Number(record.riskScore ?? 0),
        riskFactors: record.riskFactors ?? [],
        strengths: record.strengths ?? [],
        weaknesses: record.weaknesses ?? [],
        recommendedDailySavings: Number(record.recommendedDailySavings ?? 0),
        recommendedEmergencyFund: Number(
          record.recommendedEmergencyFund ?? 0
        ),
        monthsToEmergencyFund: Number(record.monthsToEmergencyFund ?? 0),
        spendingPeakDay: record.spendingPeakDay,
        spendingPeakTime: record.spendingPeakTime,
        budgetAdherence: Number(record.budgetAdherence ?? 0),
        predictedShortfallDays: record.predictedShortfallDays ?? 0,
        predictedShortfallAmount: Number(record.predictedShortfallAmount ?? 0),
        nextLowBalanceDate: record.nextLowBalanceDate?.toISOString() ?? null,
        financialHealthGrade: record.financialHealthGrade,
        insightsSummary: record.insightsSummary,
      };

      return NextResponse.json(
        { success: true, data },
        { status: 200 }
      );
    } catch (e) {
      console.log("financial-insights-latest error", e);
      return NextResponse.json(
        { success: false, message: "Internal error" },
        { status: 500 }
      );
    }
  });
}
