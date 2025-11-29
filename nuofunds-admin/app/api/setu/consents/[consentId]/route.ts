// import { NextRequest, NextResponse } from 'next/server';

// import { setuRequest } from '@/app/lib/setu';

// type RouteContext = {
// 	params: {
// 		consentId?: string;
// 	};
// };

// function extractConsentId(request: NextRequest, context?: RouteContext): string | null {
// 	const paramId = context?.params?.consentId?.trim();
// 	if (paramId) {
// 		return paramId;
// 	}

// 	const searchParams = request.nextUrl.searchParams;
// 	const queryId =
// 		searchParams.get('consentId') ??
// 		searchParams.get('requestId') ??
// 		searchParams.get('id');
// 	if (queryId?.trim()) {
// 		return queryId.trim();
// 	}

// 	const segments = request.nextUrl.pathname.split('/').filter(Boolean);
// 	const consentsIndex = segments.lastIndexOf('consents');
// 	if (consentsIndex !== -1 && consentsIndex < segments.length - 1) {
// 		const rawSegment = segments[consentsIndex + 1];
// 		if (rawSegment && rawSegment !== 'route') {
// 			try {
// 				return decodeURIComponent(rawSegment).trim();
// 			} catch {
// 				return rawSegment.trim();
// 			}
// 		}
// 	}

// 	return null;
// }

// export async function GET(request: NextRequest, context: RouteContext) {
// 	const consentId = extractConsentId(request, context);
// 	const expandedParam = request.nextUrl.searchParams.get('expanded');
// 	const expanded = expandedParam !== 'false';

// 	if (!consentId) {
// 		return NextResponse.json({ error: 'consentId or requestId is required' }, { status: 400 });
// 	}

// 	try {
// 		const path = `/v2/consents/${encodeURIComponent(consentId)}?expanded=${expanded}`;
// 		const data = await setuRequest<Record<string, unknown>>(path, { method: 'GET' });
// 		console.log('Setu consent fetch response', data);
// 		return NextResponse.json({ consent: data });
// 	} catch (error) {
// 		console.error(`Failed to fetch Setu consent ${consentId}`, error);
// 		return NextResponse.json(
// 			{
// 				error: error instanceof Error ? error.message : 'Failed to fetch consent',
// 			},
// 			{ status: 500 }
// 		);
// 	}
// }
