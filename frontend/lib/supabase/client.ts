/**
 * Supabase Client Factory.
 *
 * Creates a new Supabase client instance for use in browser/client-side components.
 * This handles authentication state persistence automatically.
 *
 * @module lib/supabase
 */

'use client' // This file is for client-side components

import { createBrowserClient } from '@supabase/ssr'

/**
 * Creates and returns a Supabase browser client.
 *
 * @returns {SupabaseClient} An authenticated Supabase client.
 */
export function createClient() {
  // Create a supabase client on the browser with project's credentials
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}