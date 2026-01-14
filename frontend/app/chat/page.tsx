/**
 * Chat Interface Component.
 *
 * Displays the main chat window where users interact with the Dining Bot.
 * Handles sending messages, displaying streaming responses, and managing
 * context filters (Dining Hall, Meal Type).
 *
 * @module app/chat/page
 */

'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import Link from 'next/link';
import { useChat } from '@ai-sdk/react';
import { TextStreamChatTransport } from 'ai';
import ReactMarkdown from 'react-markdown';

/** Represents a part of a chat message content. */
type TextPart = { type: 'text'; text: string };
/** Valid roles in the chat conversation. */
type ChatRole = 'user' | 'assistant' | 'system';
/** Message structure used by the UI. */
type ChatUIMessage = { id?: string; role: ChatRole; parts: TextPart[] };

const DINING_HALLS = ['Berkshire', 'Worcester', 'Hampshire', 'Franklin'] as const;
const MEALS = ['Breakfast', 'Lunch', 'Dinner', "Grab' n Go", 'Late Night'] as const;

// Shared state for transport callbacks (avoids ref access during render)
const sharedState = {
    userId: null as string | null,
    filters: { dining_halls: [] as string[], meals: [] as string[] },
};

// Create transport once outside component to avoid React compiler issues
const chatTransport = new TextStreamChatTransport({
    api: '/api/ai-chat',
    headers: () => ({ 'X-User-ID': sharedState.userId || '' }),
    body: () => {
        const { filters } = sharedState;
        const hasFilters = filters.dining_halls.length > 0 || filters.meals.length > 0;
        return hasFilters ? { filters } : {};
    },
});

/**
 * The main Chat Page component.
 */
export default function ChatPage() {
    const supabase = createClient();
    const router = useRouter();
    const [userId, setUserId] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [input, setInput] = useState('');

    // Filter state for dining hall and meal selection
    const [selectedHalls, setSelectedHalls] = useState<string[]>([]);
    const [selectedMeals, setSelectedMeals] = useState<string[]>([]);

    // Keep shared state in sync with component state
    useEffect(() => {
        sharedState.userId = userId;
    }, [userId]);

    useEffect(() => {
        sharedState.filters = { dining_halls: selectedHalls, meals: selectedMeals };
    }, [selectedHalls, selectedMeals]);

    const toggleHall = (hall: string) => {
        setSelectedHalls((prev) => (prev.includes(hall) ? prev.filter((h) => h !== hall) : [...prev, hall]));
    };

    const toggleMeal = (meal: string) => {
        setSelectedMeals((prev) => (prev.includes(meal) ? prev.filter((m) => m !== meal) : [...prev, meal]));
    };

    // Initialize chat hook using TextStream transport to consume plain text streams from our edge route
    const { messages, sendMessage, status, error, stop } = useChat({
        messages: [
            {
                id: 'welcome',
                role: 'assistant',
                parts: [{ type: 'text', text: "Hello! I'm your Dining Bot. How can I help you find food today?" }],
            },
        ],
        transport: chatTransport,
        onFinish() {
            // Refocus input after streaming completes.
            inputRef.current?.focus();
        },
    });

    // Auth check and initial focus.
    useEffect(() => {
        const checkUserSession = async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error || !data.user) {
                router.push('/');
            } else {
                setUserId(data.user.id);
                inputRef.current?.focus();
            }
        };
        checkUserSession();
    }, [supabase, router]);

    // Auto-scroll to latest message on update.
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <main className="flex flex-col h-screen">
            <header className="p-4 border-b shadow-sm bg-white">
                <div className="flex items-center justify-between">
                    <h1 className="text-xl font-bold text-gray-900">Dining Bot</h1>
                    <div className="flex space-x-4">
                        <Link href="/dashboard" className="text-[#881C1B] hover:underline font-medium">
                            Dashboard
                        </Link>
                        <Link href="/dashboard/log" className="text-[#881C1B] hover:underline font-medium">
                            Log Food
                        </Link>
                        <Link href="/profile" className="text-[#881C1B] hover:underline font-medium">
                            Profile
                        </Link>
                    </div>
                </div>
            </header>

            {/* Filter toggles for dining halls and meals */}
            <div className="p-3 bg-white border-b space-y-2">
                <div className="flex flex-wrap gap-2 items-center">
                    <span className="text-sm font-medium text-gray-600 mr-1">Hall:</span>
                    {DINING_HALLS.map((hall) => (
                        <button
                            key={hall}
                            type="button"
                            onClick={() => toggleHall(hall)}
                            className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                                selectedHalls.includes(hall) ? 'bg-[#881C1B] text-white border-[#881C1B]' : 'bg-white text-gray-700 border-gray-300 hover:border-[#881C1B]'
                            }`}
                        >
                            {hall}
                        </button>
                    ))}
                </div>
                <div className="flex flex-wrap gap-2 items-center">
                    <span className="text-sm font-medium text-gray-600 mr-1">Meal:</span>
                    {MEALS.map((meal) => (
                        <button
                            key={meal}
                            type="button"
                            onClick={() => toggleMeal(meal)}
                            className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                                selectedMeals.includes(meal) ? 'bg-[#881C1B] text-white border-[#881C1B]' : 'bg-white text-gray-700 border-gray-300 hover:border-[#881C1B]'
                            }`}
                        >
                            {meal}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {messages.map((m: ChatUIMessage) => (
                    <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div
                            className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                                m.role === 'user'
                                    ? 'bg-[#881C1B] text-white whitespace-pre-wrap'
                                    : 'bg-gray-200 text-gray-900 prose prose-sm prose-gray max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-strong:text-gray-900'
                            }`}
                        >
                            {m.parts?.map((part, i) =>
                                part.type === 'text' ? (
                                    m.role === 'user' ? (
                                        <span key={`${m.id}-${i}`}>{part.text}</span>
                                    ) : (
                                        <ReactMarkdown key={`${m.id}-${i}`}>{part.text}</ReactMarkdown>
                                    )
                                ) : null,
                            )}
                            {m.id === messages[messages.length - 1]?.id && status === 'streaming' && m.role === 'assistant' && <span className="ml-1 animate-pulse">▍</span>}
                        </div>
                    </div>
                ))}

                {error && (
                    <div className="flex justify-start">
                        <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-red-100 text-red-700">
                            <p>
                                <strong>Error:</strong> {String(error)}
                            </p>
                            <p className="text-sm">Please check your backend connection.</p>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    if (!input.trim()) return;
                    sendMessage({ text: input });
                    setInput('');
                }}
                className="p-4 border-t bg-white"
            >
                <div className="flex space-x-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        readOnly={status === 'submitted' || status === 'streaming'}
                        className={`flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-[#881C1B] focus:border-[#881C1B] text-gray-900 ${
                            status === 'submitted' || status === 'streaming' ? 'opacity-50' : ''
                        }`}
                        placeholder="Ask for meal plans, calories, or dining hall menus..."
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || status === 'submitted' || status === 'streaming'}
                        className="px-4 py-2 font-semibold text-white bg-[#881C1B] rounded-md hover:bg-[#6d1615] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#881C1B] disabled:opacity-50"
                    >
                        {status === 'submitted' || status === 'streaming' ? 'Streaming...' : 'Send'}
                    </button>
                    {(status === 'submitted' || status === 'streaming') && (
                        <button
                            type="button"
                            onClick={() => stop()}
                            className="px-4 py-2 font-semibold text-[#881C1B] border border-[#881C1B] rounded-md hover:bg-[#881C1B] hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#881C1B]"
                        >
                            Abort
                        </button>
                    )}
                </div>
            </form>
        </main>
    );
}