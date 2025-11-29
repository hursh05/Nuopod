import { withAuth } from "@/app/lib/middleware";
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib/prisma";

export async function GET (req: NextRequest) {
    return withAuth(req, async (req: any) => {
        const user = await prisma.customer.findUnique({
            where: { id: req.user.userId },
            select: {
                id: true,
                email: true,
                name: true,
                consent: true,
                createdAt: true,
            },
        });
        if (!user)
            return NextResponse.json({ error: "user not found" }, { status: 404 });
        return NextResponse.json({ user });
    }); 
}