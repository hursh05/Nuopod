export const urls = {
    noauth: {
        login: '/user/login',
        register: '/user/register',
    },
    auth: {
        consent: '/setu/consents',
        getConsent: '/setu/consents/get_details',
        notification: {
            manage_token: '/notification/tokens',
        },
        transactions: {
            manual: '/transactions/manual',
        },
        dashboard: '/dashboard',
        daily_details: '/dashboard/daily-features',
        forecast_details: '/dashboard/forecast-details',
        financial_insights: '/dashboard/financial-insights-latest',
        chat: '/user/chat-bot',
    }
}