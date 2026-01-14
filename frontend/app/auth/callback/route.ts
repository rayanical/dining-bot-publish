/**
 * GET /auth/callback
 *
 * Handles Supabase OAuth callback by exchanging the `code` query parameter for a session
 * and setting auth cookies. On success, redirects to `/login-check`.
 *
 * Query params:
 * - code: Authorization code from the identity provider.
 *
 * Success:
 * - 302 redirect to /login-check with session cookies set.
 *
 * Errors:
 * - If the code is missing or the exchange fails, redirects to `/?error=auth_failed`.
 */
import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
    const requestUrl = new URL(request.url);
    const code = requestUrl.searchParams.get('code');
    const origin = requestUrl.origin;

    if (code) {
        const cookieStore = await cookies();

        const supabase = createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!, {
            cookies: {
                get(name: string) {
                    return cookieStore.get(name)?.value;
                },
                set(name: string, value: string, options: CookieOptions) {
                    cookieStore.set({ name, value, ...options });
                },
                remove(name: string, options: CookieOptions) {
                    cookieStore.delete({ name, ...options });
                },
            },
        });

        const { error } = await supabase.auth.exchangeCodeForSession(code);

        if (!error) {
            return NextResponse.redirect(`${origin}/login-check`);
        }
    }

    return NextResponse.redirect(`${origin}/?error=auth_failed`);
}
