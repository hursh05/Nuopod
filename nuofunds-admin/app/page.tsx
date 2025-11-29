'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

type DashboardSession = {
	id: string;
	status: string;
	createdAt: string;
	updatedAt: string;
	requestedAt?: string | null;
	completedAt?: string | null;
};

type DashboardConsent = {
	id: string;
	status: string;
	createdAt: string;
	updatedAt: string;
	fiTypes: string[];
	fipIds: string[];
	rawRequest?: Record<string, unknown> | null;
	rawResponse?: Record<string, unknown> | null;
	sessions: DashboardSession[];
};

type DashboardTransaction = {
	id: string;
	txnDate: string;
	valueDate?: string | null;
	amount: number;
	currency: string;
	type: string;
	narration?: string | null;
	referenceNumber?: string | null;
	account?: {
		id: string;
		referenceId?: string | null;
		maskedAccountNumber?: string | null;
	};
};

type DashboardUser = {
	id: string;
	name: string | null;
	email: string | null;
	phone: string | null;
	externalId: string | null;
	createdAt: string;
	consents: DashboardConsent[];
	transactions: DashboardTransaction[];
};

type DashboardWebhookEvent = {
	id: string;
	eventName: string;
	eventType: string;
	referenceId?: string | null;
	status: string;
	createdAt: string;
	payload: unknown;
};

const HARDCODED_USER_ID = 'demo-user-id';

const DEFAULT_CONSENT_PAYLOAD = JSON.stringify(
	{
		consentDuration: {
			unit: 'MONTH',
			value: 24,
		},
		vua: '9769746180@onemoney',
		consentTypes: ['PROFILE', 'SUMMARY', 'TRANSACTIONS'],
		dataRange: {
			from: '2023-01-01T00:00:00Z',
			to: '2025-01-24T00:00:00Z',
		},
		context: [],
	},
	null,
	2,
);

const DEMO_SESSION_DEFAULT_DATE = '2025-11-11T02:49:09.051Z';

const dateFormatter = new Intl.DateTimeFormat('en-IN', {
	dateStyle: 'medium',
	timeStyle: 'short',
});

function formatDate(value?: string | null) {
	if (!value) return '—';
	try {
		return dateFormatter.format(new Date(value));
	} catch {
		return value;
	}
}

export default function Home() {
	const [users, setUsers] = useState<DashboardUser[]>([]);
	const [selectedUserId, setSelectedUserId] = useState(HARDCODED_USER_ID);

	const [consentPayload, setConsentPayload] = useState(DEFAULT_CONSENT_PAYLOAD);
	const [consentLookupId, setConsentLookupId] = useState('');

	const [statusMessage, setStatusMessage] = useState<string>('');
	const [consentDetails, setConsentDetails] = useState<Record<
		string,
		unknown
	> | null>(null);
	const [consentDetailsSource, setConsentDetailsSource] = useState<
		'persisted' | 'api' | null
	>(null);
	const [webhookEvents, setWebhookEvents] = useState<DashboardWebhookEvent[]>(
		[],
	);
	const [loadingWebhooks, setLoadingWebhooks] = useState(false);
	const [demoConsentId, setDemoConsentId] = useState('');
	const [demoDateFrom, setDemoDateFrom] = useState(DEMO_SESSION_DEFAULT_DATE);
	const [demoDateTo, setDemoDateTo] = useState(DEMO_SESSION_DEFAULT_DATE);
	const [creatingDemoSession, setCreatingDemoSession] = useState(false);
	const [demoSessionResponse, setDemoSessionResponse] = useState<Record<
		string,
		unknown
	> | null>(null);
	const [sessionLookupId, setSessionLookupId] = useState('');
	const [sessionFetchResponse, setSessionFetchResponse] = useState<Record<
		string,
		unknown
	> | null>(null);
	const [fetchingSession, setFetchingSession] = useState(false);
	const [accessTokenPayload, setAccessTokenPayload] = useState<Record<
		string,
		unknown
	> | null>(null);
	const [fetchingConsent, setFetchingConsent] = useState(false);
	const [creatingConsent, setCreatingConsent] = useState(false);
	const [creatingAccessToken, setCreatingAccessToken] = useState(false);
	const [loadingAccessToken, setLoadingAccessToken] = useState(false);
	const [refreshNonce, setRefreshNonce] = useState(0);

	const loadUsers = useCallback(async () => {
		try {
			const res = await fetch('/api/users');
			if (!res.ok) {
				throw new Error('Failed to load users');
			}
			const data = (await res.json()) as { users: DashboardUser[] };
			setUsers(data.users);
		} catch (error) {
			setStatusMessage(
				error instanceof Error ? error.message : 'Unable to load users',
			);
		}
	}, []);

	const loadAccessToken = useCallback(async () => {
		setLoadingAccessToken(true);
		try {
			const res = await fetch('/api/setu/access-token');
			if (res.status === 404) {
				setAccessTokenPayload(null);
				return;
			}
			const data = await res.json();
			if (!res.ok) {
				throw new Error(data.error ?? 'Failed to load access token');
			}
			setAccessTokenPayload(data.token as Record<string, unknown>);
		} catch (error) {
			setStatusMessage(
				error instanceof Error ? error.message : 'Unable to load access token',
			);
		} finally {
			setLoadingAccessToken(false);
		}
	}, []);

	const loadWebhookEvents = useCallback(async () => {
		setLoadingWebhooks(true);
		try {
			const res = await fetch('/api/setu/webhook-events?limit=25');
			const data = await res.json();
			if (!res.ok) {
				throw new Error(data.error ?? 'Failed to load webhook events');
			}
			setWebhookEvents(Array.isArray(data.events) ? data.events : []);
		} catch (error) {
			setStatusMessage(
				error instanceof Error
					? error.message
					: 'Unable to load webhook events',
			);
		} finally {
			setLoadingWebhooks(false);
		}
	}, []);

	useEffect(() => {
		void loadUsers();
	}, [loadUsers, refreshNonce]);

	useEffect(() => {
		void loadAccessToken();
	}, [loadAccessToken]);

	useEffect(() => {
		void loadWebhookEvents();
	}, [loadWebhookEvents, refreshNonce]);

	const selectedUser = useMemo(
		() => users.find((user) => user.id === selectedUserId),
		[selectedUserId, users],
	);
	const selectedConsent = useMemo(
		() => selectedUser?.consents[0],
		[selectedUser],
	);

	const handleFetchConsentDetails = useCallback(async () => {
		const trimmed = consentLookupId.trim();
		const consentId = trimmed || selectedConsent?.id;
		if (!consentId) {
			setStatusMessage('Provide a consent ID');
			return;
		}
		setFetchingConsent(true);
		setConsentDetailsSource(null);
		try {
			const res = await fetch(
				`/api/setu/consents/${encodeURIComponent(consentId)}?expanded=true`,
			);
			const data = await res.json();
			if (!res.ok) {
				throw new Error(data.error ?? 'Failed to fetch consent');
			}
			setConsentDetails(data.consent as Record<string, unknown>);
			setConsentDetailsSource('api');
			setStatusMessage(`Fetched consent ${consentId}`);
		} catch (error) {
			setStatusMessage(
				error instanceof Error ? error.message : 'Unable to fetch consent',
			);
		} finally {
			setFetchingConsent(false);
		}
	}, [consentLookupId, selectedConsent]);

	useEffect(() => {
		if (!selectedUser && users.length) {
			const fallback =
				users.find((user) => user.id === HARDCODED_USER_ID) ?? users[0];
			if (fallback && fallback.id !== selectedUserId) {
				setSelectedUserId(fallback.id);
			}
		}
	}, [users, selectedUser, selectedUserId]);

	useEffect(() => {
		setConsentLookupId(selectedConsent?.id ?? '');
		setDemoConsentId(selectedConsent?.id ?? '');
		const inferredRange = extractDataRange(
			selectedConsent?.rawResponse ?? null,
		);
		setDemoDateFrom(inferredRange?.from ?? DEMO_SESSION_DEFAULT_DATE);
		setDemoDateTo(inferredRange?.to ?? DEMO_SESSION_DEFAULT_DATE);
		const defaultSessionId = selectedConsent?.sessions[0]?.id ?? '';
		setSessionLookupId(defaultSessionId);
		setSessionFetchResponse(null);
		if (selectedConsent?.rawResponse) {
			setConsentDetails(selectedConsent.rawResponse);
			setConsentDetailsSource('persisted');
		} else {
			setConsentDetails(null);
			setConsentDetailsSource(null);
		}
	}, [selectedConsent]);

	function parseJsonInput(input: string) {
		try {
			return JSON.parse(input);
		} catch {
			throw new Error('Invalid JSON payload');
		}
	}

	function extractRedirectUrl(
		payload: Record<string, unknown> | null | undefined,
	) {
		if (!payload) return undefined;
		const record = payload as Record<string, unknown>;
		const candidateKeys: Array<'url' | 'redirectUrl' | 'redirect_url'> = [
			'url',
			'redirectUrl',
			'redirect_url',
		];
		for (const key of candidateKeys) {
			const value = record[key];
			if (typeof value === 'string') {
				const normalized = value.trim();
				if (normalized.length > 0) {
					return normalized;
				}
			}
		}
		return undefined;
	}

	async function handleCreateConsent() {
		setCreatingConsent(true);
		setStatusMessage('');
		try {
			const requestPayload = parseJsonInput(consentPayload);
			const res = await fetch('/api/setu/consents', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({
					request: requestPayload,
				}),
			});
			const data = (await res.json()) as {
				consent?: { id: string; rawResponse?: Record<string, unknown> | null };
				error?: string;
			};
			if (!res.ok || !data.consent?.id) {
				throw new Error(data.error ?? 'Failed to create consent');
			}
			setStatusMessage(`Created consent ${data.consent.id}`);
			if (data.consent.rawResponse) {
				setConsentDetails(data.consent.rawResponse);
				setConsentDetailsSource('api');
			}
			const redirectTarget = extractRedirectUrl(
				(data.consent.rawResponse ?? null) as Record<string, unknown> | null,
			);
			if (redirectTarget) {
				window.open(redirectTarget, '_blank', 'noopener,noreferrer');
			}
			setConsentLookupId(data.consent.id);
			setRefreshNonce((n) => n + 1);
		} catch (error) {
			setStatusMessage(
				error instanceof Error ? error.message : 'Unable to create consent',
			);
		} finally {
			setCreatingConsent(false);
		}
	}

	// 1. Update handleCreateDemoSession to save the returned session ID
	async function handleCreateDemoSession() {
		const consentId =
			demoConsentId.trim() ||
			consentLookupId.trim() ||
			selectedConsent?.id ||
			'';

		if (!consentId) {
			setStatusMessage('Provide a consent ID for the demo FI data fetch');
			return;
		}

		setCreatingDemoSession(true);
		setDemoSessionResponse(null);
		setStatusMessage('');

		try {
			const res = await fetch('/api/setu/sessions/demo', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({
					consentId,
					from: demoDateFrom,
					to: demoDateTo,
				}),
			});

			const data = await res.json();

			if (!res.ok) {
				throw new Error(data.error ?? 'Failed to create demo session');
			}

			setDemoSessionResponse(data);

			// IMPORTANT: Set the session ID for fetching
			if (data.session?.id) {
				setSessionLookupId(data.session.id);
				setStatusMessage(
					`Demo FI data fetch created! Session ID: ${data.session.id}. ` +
						`Wait a few seconds, then click "Get FI Data" to retrieve the results.`,
				);
			} else {
				setStatusMessage(`Demo FI data fetch invoked for consent ${consentId}`);
			}

			// Refresh to show new session in the list
			setRefreshNonce((n) => n + 1);
		} catch (error) {
			setStatusMessage(
				error instanceof Error
					? error.message
					: 'Unable to run demo FI data fetch',
			);
		} finally {
			setCreatingDemoSession(false);
		}
	}

	// 2. Update handleFetchSession to use the correct session ID
	async function handleFetchSession() {
		const trimmed = sessionLookupId.trim();

		if (!trimmed) {
			setStatusMessage('Provide a session ID to fetch FI data');
			return;
		}

		setFetchingSession(true);
		setSessionFetchResponse(null);
		setStatusMessage('');

		try {
			const res = await fetch(
				`/api/setu/sessions/${encodeURIComponent(trimmed)}?expanded=true`,
			);

			const data = await res.json();

			if (!res.ok) {
				throw new Error(data.error ?? 'Failed to fetch session');
			}

			setSessionFetchResponse(data.session as Record<string, unknown>);
			setStatusMessage(
				`Fetched FI session ${trimmed}. ` +
					`Status: ${(data.session as any)?.status || 'unknown'}`,
			);
		} catch (error) {
			setStatusMessage(
				error instanceof Error ? error.message : 'Unable to fetch FI session',
			);
		} finally {
			setFetchingSession(false);
		}
	}

	const handleCreateAccessToken = useCallback(async () => {
		setCreatingAccessToken(true);
		setStatusMessage('');
		try {
			const res = await fetch('/api/setu/access-token', { method: 'POST' });
			const data = await res.json();
			if (!res.ok) {
				throw new Error(data.error ?? 'Failed to create access token');
			}
			setAccessTokenPayload(data.token as Record<string, unknown>);
			await loadAccessToken();
			setStatusMessage('Created access token');
		} catch (error) {
			setStatusMessage(
				error instanceof Error
					? error.message
					: 'Unable to create access token',
			);
		} finally {
			setCreatingAccessToken(false);
		}
	}, [loadAccessToken]);

	function ConsentStatusBadge({
		consent,
	}: {
		consent: DashboardConsent | undefined;
	}) {
		if (!consent) return null;

		const statusColors: Record<string, string> = {
			ACTIVE: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
			PENDING: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
			REVOKED: 'bg-red-500/20 text-red-300 border-red-500/30',
			EXPIRED: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
			FAILED: 'bg-red-500/20 text-red-300 border-red-500/30',
		};

		const colorClass =
			statusColors[consent.status] ||
			'bg-slate-500/20 text-slate-300 border-slate-500/30';
		const accountsCount = consent.rawResponse?.accountsLinked?.length || 0;

		return (
			<div className="mt-4 space-y-2">
				<div
					className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-semibold ${colorClass}`}
				>
					<span className="relative flex h-2 w-2">
						{consent.status === 'ACTIVE' && (
							<span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
						)}
						<span
							className={`relative inline-flex h-2 w-2 rounded-full ${
								consent.status === 'ACTIVE'
									? 'bg-emerald-500'
									: consent.status === 'PENDING'
									? 'bg-yellow-500'
									: 'bg-red-500'
							}`}
						></span>
					</span>
					Status: {consent.status}
				</div>

				{consent.status === 'PENDING' && (
					<div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3 text-sm text-yellow-200">
						<p className="font-semibold">⚠️ Action Required</p>
						<p className="mt-1 text-xs">
							This consent is pending approval. Click the button below to
							complete account linking.
						</p>
						{consent.rawResponse?.url && (
							<a
								href={consent.rawResponse.url as string}
								target="_blank"
								rel="noopener noreferrer"
								className="mt-2 inline-block rounded-lg bg-yellow-400 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-yellow-300"
							>
								Complete Consent Approval →
							</a>
						)}
					</div>
				)}

				{consent.status === 'ACTIVE' && (
					<div className="text-sm text-slate-400">
						✅ {accountsCount} account{accountsCount !== 1 ? 's' : ''} linked •
						Ready to fetch data
					</div>
				)}

				{(consent.status === 'REVOKED' ||
					consent.status === 'EXPIRED' ||
					consent.status === 'FAILED') && (
					<div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">
						<p>
							❌ This consent cannot be used. Create a new consent to continue.
						</p>
					</div>
				)}
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-slate-950 text-slate-50">
			<div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10">
				<header className="rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-xl shadow-black/40">
					<h1 className="text-2xl font-semibold">Setu AA Demo Console</h1>
					<p className="mt-2 text-sm text-slate-300">
						Trigger the FIU flow end-to-end: create a user, initiate consent,
						start a session, poll FI data, and view ingested transactions.
					</p>
					<div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-slate-300">
						<p className="flex items-center gap-2">
							Active user:{' '}
							<span className="font-mono text-slate-100">
								{selectedUser?.name ?? selectedUserId}
							</span>
						</p>
						<button
							onClick={() => setRefreshNonce((n) => n + 1)}
							className="rounded-lg border border-white/10 px-3 py-1 text-xs uppercase tracking-wide text-slate-200"
						>
							Refresh Data
						</button>
						<button
							onClick={() => void handleCreateAccessToken()}
							disabled={creatingAccessToken}
							className="rounded-lg border border-emerald-300/60 px-3 py-1 text-xs uppercase tracking-wide text-emerald-200 disabled:opacity-60"
						>
							{creatingAccessToken ? 'Creating…' : 'Create Access Token'}
						</button>
					</div>
					<div className="mt-2 text-sm text-slate-300">
						{statusMessage ? (
							<p className="rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2 text-xs text-slate-200">
								{statusMessage}
							</p>
						) : (
							<p className="text-xs text-slate-500">No recent activity yet.</p>
						)}
					</div>
					{accessTokenPayload ? (
						<pre className="mt-3 max-h-48 overflow-auto rounded-xl border border-emerald-500/30 bg-slate-950/40 p-3 text-xs text-emerald-100">
							{JSON.stringify(accessTokenPayload, null, 2)}
						</pre>
					) : loadingAccessToken ? (
						<p className="mt-3 text-xs text-slate-500">Loading access token…</p>
					) : null}
				</header>

				<section className="rounded-2xl border border-white/5 bg-slate-900 p-6">
					<div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
						<div>
							<h2 className="text-lg font-semibold">Create Consent</h2>
							<p className="text-sm text-slate-400">
								Provide the body for <code>/v2/consents</code>. We will persist
								the response so you can fetch and use the consent immediately.
							</p>
						</div>
						<span className="text-xs text-slate-400">
							{selectedUser?.consents.length ?? 0} consents for this user
						</span>
					</div>
					<textarea
						className="mt-4 h-48 w-full rounded-xl border border-white/10 bg-slate-950/30 p-3 text-sm font-mono"
						value={consentPayload}
						onChange={(event) => setConsentPayload(event.target.value)}
					/>
					<div className="mt-4 flex flex-wrap items-center gap-3">
						<button
							onClick={() => void handleCreateConsent()}
							className="rounded-lg bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-60"
						>
							{creatingConsent ? 'Creating…' : 'Call /v2/consents'}
						</button>
					</div>
				</section>

				<section className="rounded-2xl border border-white/5 bg-slate-900 p-6">
					<div className="flex flex-col gap-2">
						<h2 className="text-lg font-semibold">Get Consent</h2>
						<p className="text-sm text-slate-400">
							Enter a consent id and we will call Setu to pull its latest
							status.
						</p>
					</div>
					<div className="mt-4 flex flex-col gap-3 md:flex-row">
						<input
							className="rounded-lg border border-white/10 bg-slate-950/30 px-3 py-2 text-sm"
							placeholder="Enter consent or request id"
							value={consentLookupId}
							onChange={(event) => setConsentLookupId(event.target.value)}
						/>
						<button
							onClick={() => void handleFetchConsentDetails()}
							disabled={fetchingConsent}
							className="rounded-lg bg-indigo-500/90 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
						>
							{fetchingConsent ? 'Fetching…' : 'Get Consent'}
						</button>
						{consentDetails && consentDetailsSource && (
							<ConsentStatusBadge consent={selectedConsent} />
						)}
					</div>
					{consentDetails ? (
						<p className="mt-2 text-xs text-slate-400">
							Showing{' '}
							{consentDetailsSource === 'api'
								? 'latest Setu response'
								: 'persisted response from storage'}
							.
						</p>
					) : null}
					{consentDetails ? (
						<pre className="mt-4 max-h-64 overflow-auto rounded-xl border border-white/10 bg-slate-950/30 p-4 text-xs text-slate-200">
							{JSON.stringify(consentDetails, null, 2)}
						</pre>
					) : null}
				</section>

				<section className="rounded-2xl border border-white/5 bg-slate-900 p-6">
					<div className="flex flex-col gap-2">
						<h2 className="text-lg font-semibold">Create FI Data Fetch</h2>
						<p className="text-sm text-slate-400">
							This mirrors Setu&rsquo;s sample call to <code>/v2/sessions</code>
							. Provide a consent ID and optional ISO timestamps (defaults to
							the doc example).
						</p>
					</div>
					<div className="mt-4 grid gap-3 md:grid-cols-3">
						<input
							className="rounded-lg border border-white/10 bg-slate-950/30 px-3 py-2 text-sm"
							placeholder="Consent ID"
							value={demoConsentId}
							onChange={(event) => setDemoConsentId(event.target.value)}
						/>
						<input
							className="rounded-lg border border-white/10 bg-slate-950/30 px-3 py-2 text-sm"
							placeholder="From (ISO)"
							value={demoDateFrom}
							onChange={(event) => setDemoDateFrom(event.target.value)}
						/>
						<input
							className="rounded-lg border border-white/10 bg-slate-950/30 px-3 py-2 text-sm"
							placeholder="To (ISO)"
							value={demoDateTo}
							onChange={(event) => setDemoDateTo(event.target.value)}
						/>
					</div>
					<div className="mt-4 flex flex-wrap items-center gap-3">
						<button
							onClick={() => void handleCreateDemoSession()}
							disabled={creatingDemoSession}
							className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-60"
						>
							{creatingDemoSession ? 'Calling…' : 'Create FI Fetch'}
						</button>
					</div>
					{demoSessionResponse ? (
						<pre className="mt-4 max-h-64 overflow-auto rounded-xl border border-white/10 bg-slate-950/30 p-4 text-xs text-slate-200">
							{JSON.stringify(demoSessionResponse, null, 2)}
						</pre>
					) : null}
				</section>

				<section className="rounded-2xl border border-white/5 bg-slate-900 p-6">
					<div className="flex flex-col gap-2">
						<h2 className="text-lg font-semibold">Get FI Data</h2>
						<p className="text-sm text-slate-400">
							Call <code>{'/v2/sessions/{session_id}'}</code> with any session
							you created to inspect its latest status and payload.
						</p>
					</div>
					<div className="mt-4 flex flex-col gap-3 md:flex-row">
						<input
							className="rounded-lg border border-white/10 bg-slate-950/30 px-3 py-2 text-sm"
							placeholder="Session ID"
							value={sessionLookupId}
							onChange={(event) => setSessionLookupId(event.target.value)}
						/>
						<button
							onClick={() => void handleFetchSession()}
							disabled={fetchingSession}
							className="rounded-lg bg-lime-400 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-60"
						>
							{fetchingSession ? 'Fetching…' : 'Get FI Data'}
						</button>
					</div>
					<p className="mt-2 text-xs text-slate-400">
						Enter any session ID stored in Setu to view its latest status.
					</p>
					{sessionFetchResponse ? (
						<pre className="mt-4 max-h-64 overflow-auto rounded-xl border border-white/10 bg-slate-950/30 p-4 text-xs text-slate-200">
							{JSON.stringify(sessionFetchResponse, null, 2)}
						</pre>
					) : null}
				</section>

				<section className="rounded-2xl border border-white/5 bg-slate-900 p-6">
					<div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
						<div>
							<h2 className="text-lg font-semibold">Webhook Payloads</h2>
							<p className="text-sm text-slate-400">
								We save every POST to <code>/api/setu/webhook</code>. Use this
								feed to inspect what Setu sent us.
							</p>
						</div>
						<button
							onClick={() => void loadWebhookEvents()}
							disabled={loadingWebhooks}
							className="rounded-lg border border-white/10 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
						>
							{loadingWebhooks ? 'Refreshing…' : 'Refresh'}
						</button>
					</div>
					<div className="mt-4 space-y-3">
						{webhookEvents.length === 0 ? (
							<p className="text-sm text-slate-400">
								{loadingWebhooks
									? 'Loading webhook payloads…'
									: 'No webhook payloads recorded yet.'}
							</p>
						) : (
							webhookEvents.map((event) => (
								<div
									key={event.id}
									className="rounded-xl border border-white/10 bg-slate-950/20 p-4 text-sm text-slate-200"
								>
									<div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
										<div>
											<p className="text-base font-semibold text-white">
												{event.eventName}
											</p>
											<p className="text-xs text-slate-400">
												{formatDate(event.createdAt)}
											</p>
										</div>
										<div className="text-right text-xs text-slate-400">
											<p className="font-mono uppercase tracking-wide text-emerald-300">
												{event.status}
											</p>
											<p className="text-[11px] text-slate-400">
												Type {event.eventType}
											</p>
										</div>
									</div>
									<p className="mt-2 text-xs text-slate-400">
										Reference {event.referenceId ?? '—'}
									</p>
									<pre className="mt-3 max-h-64 overflow-auto rounded-lg border border-white/10 bg-slate-950/40 p-3 text-xs text-slate-100">
										{JSON.stringify(event.payload, null, 2)}
									</pre>
								</div>
							))
						)}
					</div>
				</section>
			</div>
		</div>
	);
}
function extractDataRange(payload: Record<string, unknown> | null | undefined) {
	if (!payload) return null;
	const maybeRange = (value: unknown) => {
		if (!value || typeof value !== 'object') return null;
		const candidate = value as Record<string, unknown>;
		const from =
			typeof candidate.from === 'string' ? candidate.from : undefined;
		const to = typeof candidate.to === 'string' ? candidate.to : undefined;
		if (from || to) {
			return { from, to };
		}
		return null;
	};

	const directRange = maybeRange(payload.dataRange);
	if (directRange) return directRange;

	const detail = payload.detail as Record<string, unknown> | undefined;
	const detailRange =
		maybeRange(detail?.dataRange) ??
		maybeRange(detail?.data_range) ??
		maybeRange(detail?.consentDateRange) ??
		maybeRange(detail?.consent_date_range);
	if (detailRange) return detailRange;

	const rootConsentRange =
		maybeRange(payload.consentDateRange) ??
		maybeRange(payload.consent_date_range);
	if (rootConsentRange) return rootConsentRange;

	return null;
}
