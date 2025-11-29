import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const url = new URL(req.url);

  const success = url.searchParams.get("success") ?? "";
  const consentId = url.searchParams.get("id") ?? "";
  const errorcode = url.searchParams.get("errorcode") ?? "";
  const errormsg = url.searchParams.get("errormsg") ?? "";

  console.log("success >>", success);
  console.log("consentId >>", consentId);
  console.log("errorcode >>", errorcode);
  console.log("errormsg >>", errormsg);
  console.log("url >>", url);
  
  const redirectUrl = process.env.NODE_ENV === "development"
  ? "exp://zgmgl10-shubhammore1251-8081.exp.direct/--/consentScreen"   // expo go
  : "nuofunds://consentScreen";               // real build

  // your app scheme
  const deepLink =
    `${redirectUrl}` +
    `?success=${encodeURIComponent(success)}` +
    `&consentId=${encodeURIComponent(consentId)}` +
    `&errorcode=${encodeURIComponent(errorcode)}` +
    `&errormsg=${encodeURIComponent(errormsg)}`;

  return NextResponse.redirect(deepLink, {
    status: 302,
    headers: {
      "Cache-Control": "no-cache",
    },
  });
}
