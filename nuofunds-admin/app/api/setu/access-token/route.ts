import { NextResponse } from 'next/server';

import { env } from '@/app/lib/env';
import { prisma } from '@/app/lib/prisma';
import { v4 as uuidv4 } from 'uuid';

const ORG_SERVICE_URL = 'https://orgservice-prod.setu.co/v1/users/login';

type TokenResponse = {
	access_token: string;
	refresh_token?: string | null;
};

export async function GET() {
	try {
		const data = await prisma.setuAccessToken.findFirst();
		if (!data) {
			return NextResponse.json(
				{ error: 'No access token found' },
				{ status: 404 },
			);
		}
		return NextResponse.json({
			accessToken: data.accessToken,
			refreshToken: data.refreshToken,
		});
	} catch (error) {
		console.error('Failed to read access token', error);
		return NextResponse.json(
			{
				error:
					error instanceof Error
						? error.message
						: 'Failed to read access token',
			},
			{ status: 500 },
		);
	}
}

export async function POST() {
	try {
		const response = await fetch(ORG_SERVICE_URL, {
			method: 'POST',
			headers: {
				client: 'bridge',
				'content-type': 'application/json',
			},
			body: JSON.stringify({
				clientID: env.SETU_CLIENT_ID,
				grant_type: 'client_credentials',
				secret: env.SETU_CLIENT_SECRET,
			}),
			cache: 'no-store',
		});

		if (!response.ok) {
			const errorText = await response.text();
			throw new Error(
				`Org Service request failed (${response.status}): ${errorText}`,
			);
		}

		const data = (await response.json()) as TokenResponse;
		if (!data?.access_token) {
			throw new Error('Org Service response missing access_token');
		}

		await prisma.setuAccessToken.deleteMany();
		await prisma.setuAccessToken.create({
			data: {
				id: uuidv4(),
				accessToken: data.access_token,
				refreshToken: data.refresh_token ?? '',
			},
		});
		return NextResponse.json({
			success: true,
			data: {
				accessToken: data.access_token,
				refreshToken: data.refresh_token,
			},
			message: 'access token created successfully',
		}, { status: 201 });
	} catch (error) {
		console.error('Failed to create access token', error);
		return NextResponse.json(
			{
				error:
					error instanceof Error
						? error.message
						: 'Failed to create access token',
			},
			{ status: 500 },
		);
	}
}
