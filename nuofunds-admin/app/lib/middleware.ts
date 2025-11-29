import { hashPassword } from "@/app/lib/authentication";
import { NextRequest, NextResponse } from "next/server";
import jwt from "jsonwebtoken";

export function withAuth(req: any, handler: any) {
  const token = req.headers.get("Authorization")?.replace("Bearer ", "");
  if (!token)
    return NextResponse.json({ success: false, message: "Unauthorized" }, { status: 401 });

  console.log("token >>", token);

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!);
    req.user = decoded;
    console.log("decoded >>", decoded);
    return handler(req);
  } catch (error) {
    return NextResponse.json({ success: false, message: "Invalid token" }, { status: 401 });
  }
}
