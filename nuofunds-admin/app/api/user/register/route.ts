import { NextRequest, NextResponse } from "next/server";
import { prisma } from '@/app/lib/prisma';
import { hashPassword, signToken } from "@/app/lib/authentication";
import { v4 as uuidv4 } from 'uuid';


export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { name, email, password, phone } = body ?? {};

    if (!email || !password) {
      return NextResponse.json({ success: false, message: "email, password, phone and name required" }, { status: 400 });   
    }

    const existing = await prisma.customer.findUnique({ where: { email } });
    if (existing) {
      return NextResponse.json({success: false, message: "email already exists" }, { status: 409 });
    }

    const hashed = await hashPassword(password);
    
    const user = await prisma.customer.create({
      data: { id: uuidv4(), email, name: name, password: hashed, phone: phone },
      select: { id: true, email: true, name: true, consent: true, phone: true },
    });

    const token = signToken({ userId: user.id, email: user.email });

    const userData = {
      ...user,
      token: token,
    };

    return NextResponse.json({ 
      success: true,
      data: userData,
      message: "user registered successfully",
     }, { status: 201 });
  } catch (err) {
    console.error("signup error", err);
    return NextResponse.json({ success: false, message: "server error" }, { status: 500 });
  }
}