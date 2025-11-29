import { PrismaClient } from '@/generated/prisma/client';

declare global {
	// Using `var` is required to augment the global namespace for hot reloads.
	var prisma: PrismaClient | undefined;
}

export const prisma =
	global.prisma ??
	new PrismaClient({
		log:
			process.env.NODE_ENV === 'development'
				? ['query', 'info', 'warn', 'error']
				: ['error'],
	});

if (process.env.NODE_ENV !== 'production') {
	global.prisma = prisma;
}
