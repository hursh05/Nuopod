// app/api/goals/route.ts
import { withAuth } from "@/app/lib/middleware";
import { NextResponse } from "next/server";
import { prisma } from "@/app/lib/prisma";
import { v4 as uuidv4 } from "uuid";

export async function POST(req: Request) {
  return withAuth(req, async (req: any) => {
    try {
      const body = await req.json();

      const {
        goalName,
        goalAmount,
        targetMode, // e.g. "BY_DATE" | "BY_TENURE" | "OPEN"
        targetDate, // ISO string or null
        tenureDays,
        tenureMonths,
        priority, // e.g. "HIGH" | "MEDIUM" | "LOW"
        purposeCategory, // e.g. "TRAVEL" | "EDUCATION"
        notes,
      } = body;

      if (!goalName || !goalAmount || !targetMode) {
        return NextResponse.json(
          { error: "goalName, goalAmount and targetMode are required" },
          { status: 400 }
        );
      }

      const amountNum = Number(goalAmount);
      if (Number.isNaN(amountNum) || amountNum <= 0) {
        return NextResponse.json(
          { error: "goalAmount must be a positive number" },
          { status: 400 }
        );
      }

      let parsedTargetDate: Date | null = null;
      if (targetDate) {
        const d = new Date(targetDate);
        if (isNaN(d.getTime())) {
          return NextResponse.json(
            { error: "Invalid targetDate" },
            { status: 400 }
          );
        }
        parsedTargetDate = d;
      }

      await prisma.goal.create({
        data: {
          id: uuidv4(),
          userId: req.user.userId,
          goalName: goalName.trim(),
          goalAmount: amountNum,
          targetMode,
          targetDate: parsedTargetDate,
          tenureDays: tenureDays ? Number(tenureDays) : null,
          tenureMonths: tenureMonths ? Number(tenureMonths) : null,
          priority: priority || null,
          purposeCategory: purposeCategory || null,
          notes: notes || null,
        },
      });

      return NextResponse.json(
        {
          success: true,
          data: null,
          message: "Goal created",
        },
        { status: 201 }
      );
    } catch (error) {
      console.log("goals/route error", error);
      return NextResponse.json(
        { success: false, error: "server error" },
        { status: 500 }
      );
    }
  });
}
