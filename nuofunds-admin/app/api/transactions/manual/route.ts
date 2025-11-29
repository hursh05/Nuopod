import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib/prisma";
import { withAuth } from "@/app/lib/middleware";
import { v4 as uuidv4 } from 'uuid';

export async function POST(req: NextRequest) {
  return withAuth(req, async (req: any) => {
    try {
      const {
        mode, // "FT" | "CASH" | "UPI" | "CARD" | "OTHER"
        customMode, // string when mode === "OTHER"
        type, // "CREDIT" | "DEBIT"
        txnid, // optional
        amount,
        balance,
        dateTime, // ISO string from app
        comment, // textarea
      } = await req.json();

      if (!mode || !type || !amount || !dateTime) {
        return NextResponse.json(
          { success: false, message: "mode, type, amount and dateTime required" },
          { status: 400 }
        );
      }

      const finalMode = mode === "OTHER" ? customMode?.trim() || "OTHER" : mode;

      const parsedAmount = Number(amount);
      const parsedBalance =
        balance !== undefined && balance !== null && balance !== ""
          ? Number(balance)
          : null;

      if (Number.isNaN(parsedAmount) || parsedAmount <= 0) {
        return NextResponse.json(
          { success: false, message:  "amount must be a positive number" },
          { status: 400 }
        );
      }

      const txDate = new Date(dateTime);
      if (isNaN(txDate.getTime())) {
        return NextResponse.json(
          { error: "Invalid dateTime" },
          { status: 400 }
        );
      }

      // create manual transaction
      const tx = await prisma.transaction.create({
        data: {
          id: uuidv4(),
          userId: req.user.userId,
          mode: finalMode,
          type,
          txnId: txnid || null,
          amount: parsedAmount,
          balance: parsedBalance,
          narration: null, // you can add extra field later if needed
          reference: null,
          comment: comment || null,
          date: txDate,
          valueData: new Date(),
          fiType: "DEPOSIT", // mark it as manual internally
          financialAccountId: null, // or some account if you add picker later
        },
      });

      return NextResponse.json(
        {
          success: true,
          transaction: tx,
          message: "Manual transaction saved",
        },
        { status: 201 }
      );
    } catch (error) {
      console.log("transaction/manual error", error);
      return NextResponse.json({ error: "server error" }, { status: 500 });
    }
  });
}
