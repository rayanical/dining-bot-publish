/**
 * POST /api/chat
 *
 * Accepts a chat transcript and proxies the latest user message to the FastAPI backend.
 *
 * Request body:
 * - messages: Array of { role: 'user' | 'assistant' | 'system'; content: string }
 * - user_id?: string (optional Supabase user id to enrich responses)
 *
 * Success:
 * - 200 with a streaming text/plain body of the assistant response (RAG+LLM output).
 *
 * Errors:
 * - 400 if no user message is present.
 * - 502 if the backend returns a non-OK response or empty body.
 * - 500 if an unexpected error occurs while handling the request.
 */
export const runtime = 'edge';
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const FASTAPI_URL = `${BASE_URL}/api/chat`;

type ChatMessage = { id?: string; role: 'user' | 'assistant' | 'system'; content: string };

export async function POST(req: Request) {
    try {
        const { messages, user_id } = await req.json();

        const lastUserMessage: ChatMessage | undefined = (messages as ChatMessage[])
            .slice()
            .reverse()
            .find((m) => m.role === 'user');

        if (!lastUserMessage) {
            return new Response('No user message found', { status: 400 });
        }

        const response = await fetch(FASTAPI_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: lastUserMessage.content, user_id: user_id ?? null }),
        });

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
        // Log unexpected server-side errors for observability (allowed top-level handler)
        console.error('Chat route error:', error);
        const message = error instanceof Error ? error.message : 'Unknown error';
        const errorStream = new ReadableStream({
            start(controller) {
                controller.enqueue(`An error occurred: ${message}`);
                controller.close();
            },
        });
        return new Response(errorStream, { status: 500, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
    }
}
