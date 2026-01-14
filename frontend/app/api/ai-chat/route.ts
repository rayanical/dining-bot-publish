/**
 * AI Chat Streaming Route (Edge Runtime).
 *
 * This endpoint acts as an edge proxy between the frontend client and the 
 * Python/FastAPI backend. It forwards user messages or prompts to the backend
 * and streams the text response back to the client.
 *
 * @module api/ai-chat
 */

// Use Edge runtime for lower latency streaming
export const runtime = 'edge';

/**
 * Interface definition for global process variable in Edge runtime.
 */
interface GlobalWithProcess {
    process?: { env?: { BACKEND_URL?: string } };
}

/**
 * The backend URL derived from environment variables.
 * Falls back to localhost if not defined.
 */
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const FASTAPI_URL = `${BASE_URL}/api/chat`;

/**
 * POST handler for the AI chat endpoint.
 *
 * Accepts a JSON body containing either a full message history (`messages`)
 * or a single prompt (`prompt`).
 *
 * @param {Request} req - The incoming request object.
 * @returns {Promise<Response>} A streaming response containing the AI's text output.
 */
export async function POST(req: Request) {
    try {
        const body = await req.json();
        let response: Response;

        // Prefer forwarding full messages (for memory). Fallback to single prompt format.
        if (body.messages && Array.isArray(body.messages)) {
            const user_id = req.headers.get('X-User-ID') || null;
            // Forward manual filters if provided
            const filters = body.filters || null;
            response = await fetch(FASTAPI_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: body.messages,
                    user_id,
                    filters,
                }),
            });
        } else if (body.prompt) {
            response = await fetch(FASTAPI_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: body.prompt,
                    user_id: body.user_id || null,
                }),
            });
        } else {
            return new Response('No prompt found', { status: 400 });
        }

        if (!response.ok) {
            const errorText = await response.text();
            return new Response(`FastAPI backend error: ${response.status} ${errorText}`, { status: 502 });
        }

        if (!response.body) {
            return new Response('FastAPI backend returned an empty response body', { status: 502 });
        }

        return new Response(response.body, {
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
        });
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        return new Response(`An error occurred: ${message}`, { status: 500 });
    }
}