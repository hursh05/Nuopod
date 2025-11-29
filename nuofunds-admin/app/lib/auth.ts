import { betterAuth } from 'better-auth';
import { prismaAdapter } from 'better-auth/adapters/prisma';
import { prisma } from '@/app/lib/prisma';
import { expo } from '@better-auth/expo';

export const auth = betterAuth({
	plugins: [expo()],
	database: prismaAdapter(prisma, {
		provider: 'postgresql',
	}),
	emailAndPassword: {
		enabled: true,
	},
	trustedOrigins: ['nuofunds://'],
});
