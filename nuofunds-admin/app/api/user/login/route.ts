import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/app/lib/prisma";
import { signToken, verifyPassword } from "@/app/lib/authentication";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, password } = body ?? {};

    console.log("body >>", body);


    if (!email || !password) {
      return NextResponse.json(
        { success: false, message: "email and password required" },
        { status: 400 }
      );
    }

    const user = await prisma.customer.findUnique({
      where: { email: email },
      select: {
        id: true,
        email: true,
        name: true,
        password: true,
        consent: true,
        createdAt: true,
      },
    });

    if (!user)
      return NextResponse.json({success: false, message: "user not found" }, { status: 404 });

    const valid = await verifyPassword(password, user.password);
    if (!valid)
      return NextResponse.json({success: false, message: "invalid password" }, { status: 401 });

    const token = signToken({ userId: user.id, email: user.email });

    const userData = {
      id: user.id,
      email: user.email,
      name: user.name,
      consent: user.consent,
      createdAt: user.createdAt,
      token: token,
    };

    return NextResponse.json({ 
      success: true,
      data: userData,
      message: "user logged in successfully",
     }, { status: 200 });
  } catch (err) {
    console.error("me error", err);
    return NextResponse.json({ success: false, message: "server error" }, { status: 500 });
  }
}
