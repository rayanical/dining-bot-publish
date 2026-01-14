/**
 * Login Check Redirector.
 *
 * This page acts as an interstitial router. After a successful OAuth login,
 * it checks if the user already has a profile in the backend.
 *
 * - If profile exists -> Redirect to `/chat`.
 * - If profile missing (404) -> Redirect to `/onboarding`.
 * - If not logged in -> Redirect to `/`.
 *
 * @module app/login-check/page
 */

'use client';

import { useEffect } from 'react';
import { createClient } from '@/lib/supabase/client';
import { useRouter } from 'next/navigation';

export default function LoginCheck() {
    const supabase = createClient();
    const router = useRouter();

    useEffect(() => {
        const checkUserSession = async () => {
            const { data, error } = await supabase.auth.getUser();

            if (error) {
                router.push('/');
                return;
            }

            if (data.user) {
                // Check if profile exists in backend
                try {
                    const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/profile/${data.user.id}`);
                    if (resp.ok) {
                        router.push('/chat');
                        return;
                    } else if (resp.status === 404) {
                        router.push('/onboarding');
                        return;
                    } else {
                        // Fallback for other errors (e.g. server down), send to onboarding or error page
                        router.push('/onboarding');
                        return;
                    }
                } catch {
                    router.push('/onboarding');
                    return;
                }
            }
        };

        checkUserSession();
    }, [supabase, router]);

    return (
        <main className="flex flex-col items-center justify-center h-screen bg-gray-50">
            <div className="w-full max-w-md p-8 space-y-6 bg-white shadow-md rounded-lg">
                <h1 className="text-3xl font-bold text-center text-gray-900">Welcome to Onboarding!</h1>
                <p className="text-center text-gray-700">Login status checking..</p>
                <p className="text-center text-sm text-gray-500">Console</p>
            </div>
        </main>
    );
}