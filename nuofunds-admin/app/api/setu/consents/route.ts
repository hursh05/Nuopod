import { NextRequest, NextResponse } from "next/server";

import { prisma } from "@/app/lib/prisma";
import { DEFAULT_SETU_BASE_URL } from "@/app/lib/constants";
import { env } from "@/app/lib/env";
import {
  ConsentType,
  FinancialInformationType,
} from "@/generated/prisma/enums";
import { withAuth } from "@/app/lib/middleware";
import { v4 as uuidv4 } from 'uuid';


const CONSENT_ENDPOINT = "/v2/consents";
const CONSENT_PAYLOAD = {
  consentDuration: {
    unit: "MONTH",
    value: 24,
  },
  vua: "9769746180@onemoney",
  consentTypes: ["PROFILE", "SUMMARY", "TRANSACTIONS"],
  dataRange: {
    from: "2023-01-01T00:00:00Z",
    to: "2025-01-24T00:00:00Z",
  },
  context: [],
};

export async function GET(request: NextRequest) {
  return withAuth(request, async (req: any) => {
    try {
      const user = await prisma.customer.findUnique({
        where: { id: req.user.userId },
      });
      if (!user) {
        return NextResponse.json(
          { success: false, message: "User not found" },
          { status: 404 }
        );
      }

      const tokens = await prisma.setuAccessToken.findFirst();
      if (!tokens) {
        return NextResponse.json(
          { error: "No access token found" },
          { status: 404 }
        );
      }

      // authenticate user and get user phone number.
      // const phone = '1234567899';
      const phone = user.phone;
      CONSENT_PAYLOAD.vua = phone as string;
      const response = await fetch(DEFAULT_SETU_BASE_URL + CONSENT_ENDPOINT, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          Authorization: tokens.accessToken,
          "x-product-instance-id": env.SETU_PRODUCT_INSTANCE_ID,
          "x-client-id": env.SETU_CLIENT_ID,
          client_id: env.SETU_CLIENT_ID,
          "x-client-secret": env.SETU_CLIENT_SECRET,
          client_secret: env.SETU_CLIENT_SECRET,
          product_instance_id: env.SETU_PRODUCT_INSTANCE_ID,
          "x-module": "AA",
          module: "AA",
        },
        body: JSON.stringify(CONSENT_PAYLOAD),
        cache: "no-store",
      });

      const consentData = await response.json();
      // const consentData = {
      // 	id: '3dcce29e-91bc-40a0-9efd-ad44fb54d1c7',
      // 	url: 'https://fiu-uat.setu.co/v2/consents/webview/3dcce29e-91bc-40a0-9efd-ad44fb54d1c7',
      // 	status: 'PENDING',
      // 	detail: {
      // 		consentMode: 'STORE',
      // 		frequency: { value: 1, unit: 'HOUR' },
      // 		vua: '1234567899@onemoney',
      // 		consentStart: '2025-11-17T04:37:27.420Z',
      // 		fiTypes: ['DEPOSIT', 'RECURRING_DEPOSIT', 'TERM_DEPOSIT'],
      // 		dataRange: {
      // 			from: '2023-01-01T00:00:00.000Z',
      // 			to: '2025-01-24T00:00:00.000Z',
      // 		},
      // 		fetchType: 'PERIODIC',
      // 		purpose: {
      // 			category: [Object],
      // 			code: '102',
      // 			text: 'To verify your income and calculate loan offer',
      // 			refUri: 'https://api.rebit.org.in/aa/purpose/102.xml',
      // 		},
      // 		dataLife: { value: 1, unit: 'DAY' },
      // 		consentTypes: ['PROFILE', 'SUMMARY', 'TRANSACTIONS'],
      // 		consentExpiry: '2027-11-17T04:37:27.420Z',
      // 	},
      // 	redirectUrl: 'https://zonked-jamee-spatially.ngrok-free.dev',
      // 	context: [],
      // 	PAN: '',
      // 	usage: { lastUsed: null, count: '0' },
      // 	accountsLinked: [],
      // 	tags: [],
      // 	traceId: '1-691aa687-3e7b76d517b2244a79e4f17c',
      // };

      if (consentData.status === "PENDING") {
        await prisma.accountAggregatorConsent.create({
          data: {
            id: uuidv4(),
            userId: user.id,
            consentId: consentData.id,
            consentMode: consentData.detail.consentMode as "STORE",
            fetchType: consentData.detail.fetchType as "PERIODIC",
            pan: consentData.PAN,
            purposeCode: consentData.detail.purpose.code,
            url: consentData.url,
            vua: consentData.detail.vua,
            consentExpiry: consentData.detail.consentExpiry,
            consentStart: consentData.detail.consentStart,
            consentTypes: consentData.detail.consentTypes as ConsentType[],
            dataLifeUnit: consentData.detail.dataLife.unit,
            dataLifeValue: consentData.detail.dataLife.value,
            dataRangeFromDate: consentData.detail.dataRange.from,
            dataRangeToDate: consentData.detail.dataRange.to,
            fiTypes: consentData.detail.fiTypes as FinancialInformationType[],
            frequencyUnit: consentData.detail.frequency.unit,
            frequencyValue: consentData.detail.frequency.value,
            tags: consentData.tags,
            createdAt: new Date(),
            status: consentData.status,
          },
        });
        return NextResponse.json(
          {
            success: true,
            data: {
              url: consentData.url,
            },
          },
          { status: 200 }
        );
      }
      return NextResponse.json(
        { message: "something went wrong" },
        { status: 400 }
      );
    } catch (error) {
      console.error("Failed to create Setu consent", error);
      return NextResponse.json(
        {
          error:
            error instanceof Error ? error.message : "Failed to create consent",
        },
        { status: 500 }
      );
    }
  });
}
