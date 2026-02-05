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

import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { useRouter } from 'next/navigation';

export default function LoginCheck() {
    const supabase = createClient();
    const router = useRouter();
    const [statusMessage, setStatusMessage] = useState("Verifying your profile...");

    useEffect(() => {
        let timeoutId: NodeJS.Timeout;
        let isComplete = false;

        const checkUserSession = async () => {
            // Set a timer to update the status message after 3 seconds
            timeoutId = setTimeout(() => {
                if (!isComplete) {
                    setStatusMessage("Waking up the server (this may take up to a minute)...");
                }
            }, 3000);

            try {
                const { data, error } = await supabase.auth.getUser();

                if (error) {
                    isComplete = true;
                    clearTimeout(timeoutId);
                    router.push('/');
                    return;
                }

                if (data.user) {
                    // Check if profile exists in backend
                    try {
                        const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/profile/${data.user.id}`);
                        isComplete = true;
                        clearTimeout(timeoutId);
                        
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
                        isComplete = true;
                        clearTimeout(timeoutId);
                        router.push('/onboarding');
                        return;
                    }
                }
            } catch {
                isComplete = true;
                clearTimeout(timeoutId);
                router.push('/');
            }
        };

        checkUserSession();

        // Cleanup on unmount
        return () => {
            isComplete = true;
            clearTimeout(timeoutId);
        };
    }, [supabase, router]);

    return (
        <main className="flex flex-col items-center justify-center h-screen bg-gray-50">
            <div className="flex flex-col items-center space-y-4">
                <div className="w-10 h-10 border-4 border-gray-300 border-t-[#881C1B] rounded-full animate-spin"></div>
                <p className="text-gray-600">{statusMessage}</p>
            </div>
        </main>
    );
}