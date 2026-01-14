/**
 * Dashboard Page.
 *
 * Displays a summary of the user's daily nutritional intake versus their goals.
 * Includes a progress bar for macros and a history table of logged items.
 *
 * @module app/dashboard/page
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type MacroSummary = {
    total: number;
    target: number;
};

type HistoryItem = {
    id: number;
    item: string;
    calories: number;
    protein: number;
    meal: string;
};

type DailySummary = {
    status: string;
    date: string;
    goal: string | null;
    calories: MacroSummary;
    protein: MacroSummary;
    history: HistoryItem[];
};

/**
 * Progress bar component for displaying nutrient consumption.
 */
function ProgressBar({ label, summary }: { label: string; summary: MacroSummary }) {
    const pct = summary.target > 0 ? Math.min(100, Math.round((summary.total / summary.target) * 100)) : 0;
    return (
        <div className="space-y-1">
            <div className="flex items-center justify-between text-sm text-gray-700">
                <span className="font-medium">{label}</span>
                <span>
                    {Math.round(summary.total)} / {Math.round(summary.target)}
                </span>
            </div>
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-[#881C1B]" style={{ width: `${pct}%` }} />
            </div>
            <p className="text-xs text-gray-500">{pct}% of target</p>
        </div>
    );
}

/**
 * Table component listing logged food items for the day.
 */
function HistoryTable({
    items,
    onDelete,
}: {
    items: HistoryItem[];
    onDelete: (id: number) => void;
}) {
    if (items.length === 0) {
        return <p className="text-sm text-gray-500">No food logged for this day.</p>;
    }

    return (
        <div className="mt-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Food History</h2>
            <div className="overflow-hidden border rounded-lg">
                <table className="w-full text-sm">
                    <thead className="bg-gray-100">
                        <tr>
                            <th className="px-3 py-2 text-left">Food</th>
                            <th className="px-3 py-2 text-left">Meal</th>
                            <th className="px-3 py-2 text-left">Calories</th>
                            <th className="px-3 py-2 text-left">Protein (g)</th>
                            <th className="px-3 py-2 text-right">Delete</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.map((entry) => (
                            <tr key={entry.id} className="border-t">
                                <td className="px-3 py-2">{entry.item}</td>
                                <td className="px-3 py-2 capitalize">{entry.meal}</td>
                                <td className="px-3 py-2">{entry.calories}</td>
                                <td className="px-3 py-2">{entry.protein}</td>
                                <td className="px-3 py-2 text-right">
                                    <button
                                        onClick={() => onDelete(entry.id)}
                                        className="text-red-600 hover:text-red-800"
                                    >
                                        🗑️
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function GoalSlider({
    label,
    min,
    max,
    step,
    value,
    onChange,
}: {
    label: string;
    min: number;
    max: number;
    step: number;
    value: number;
    onChange: (val: number) => void;
}) {
    return (
        <div className="space-y-1">
            <label className="text-sm font-medium">
                {label}: {value}
            </label>
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={(e) => onChange(Number(e.target.value))}
                className="w-full"
            />
        </div>
    );
}

/**
 * Main Dashboard Page component.
 */
export default function DashboardPage() {
    const supabase = createClient();
    const router = useRouter();

    const [userId, setUserId] = useState<string | null>(null);
    const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().slice(0, 10));
    const [summary, setSummary] = useState<DailySummary | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const [editingGoals, setEditingGoals] = useState(false);
    const [customCalories, setCustomCalories] = useState(2000);
    const [customProtein, setCustomProtein] = useState(100);

    useEffect(() => {
        const checkAuth = async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error || !data.user) {
                router.push('/login');
                return;
            }
            setUserId(data.user.id);
        };
        checkAuth();
    }, [router, supabase]);

    const fetchSummary = useCallback(async () => {
        if (!userId) return;
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${BACKEND_URL}/api/users/${userId}/daily-summary?date=${selectedDate}`);
            if (!res.ok) {
                throw new Error(`Failed to load summary (status ${res.status})`);
            }
            const json: DailySummary = await res.json();
            setSummary(json);

            setCustomCalories(json.calories.target);
            setCustomProtein(json.protein.target);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to load summary';
            setError(message);
            setSummary(null);
        } finally {
            setLoading(false);
        }
    }, [selectedDate, userId]);

    useEffect(() => {
        fetchSummary();
    }, [fetchSummary]);

    if (!userId) {
        return (
            <main className="flex items-center justify-center h-screen bg-gray-50">
                <p className="text-gray-600">Checking session...</p>
            </main>
        );
    }

    const handleSaveGoals = async () => {
        if (!userId) return;

        try {
            const res = await fetch(`${BACKEND_URL}/api/users/${userId}/goals`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ calories: customCalories, protein: customProtein }),
            });

            if (!res.ok) {
                throw new Error(`Failed to save goals (status ${res.status})`);
            }

            await fetchSummary();
            setEditingGoals(false);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to save goals';
            setError(message);
        }
    };

    const handleDeleteEntry = async (logId: number) => {
        if (!userId) return;

        await fetch(`${BACKEND_URL}/api/users/${userId}/log-food/${logId}`, {
            method: 'DELETE',
        });

        fetchSummary();
    };

    return (
        <main className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-3xl mx-auto bg-white shadow-sm rounded-lg p-6 space-y-6">
                <header className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Nutrition Dashboard</h1>
                        <p className="text-sm text-gray-600">Daily intake vs targets</p>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => router.push('/chat')} className="px-4 py-2 rounded-md bg-gray-900 text-white hover:bg-gray-700 text-sm">
                            Chat
                        </button>
                            <button
                                onClick={() => router.push('/dashboard/log')}
                                className="px-4 py-2 rounded-md bg-[#881C1B] text-white hover:bg-[#6d1615] text-sm"
                            >
                                Log Food
                            </button>
                            <button
                                onClick={() => router.push('/meal-builder')}
                                className="px-4 py-2 rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm"
                            >
                                Meal Builder
                            </button>
                    </div>
                </header>

                <div className="flex flex-wrap items-center gap-3">
                    <label className="text-sm font-medium text-gray-700">Date:</label>
                    <input
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-md"
                    />
                </div>

                {loading && <p className="text-gray-600 text-sm">Loading summary...</p>}
                {error && <p className="text-red-600 text-sm">{error}</p>}

                {summary && !loading && !error && (
                    <section className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="font-semibold text-gray-900">Goal</p>
                                <p className="text-gray-600">{summary.goal || 'Not set'}</p>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setEditingGoals((prev) => !prev)}
                                    className="px-3 py-1 bg-gray-200 rounded text-sm"
                                >
                                    {editingGoals ? 'Close' : 'Edit Goals'}
                                </button>
                            </div>
                        </div>

                        {editingGoals && (
                            <div className="p-4 mt-2 border rounded bg-gray-50 space-y-4">
                                <GoalSlider
                                    label="Calories"
                                    min={1200}
                                    max={4000}
                                    step={50}
                                    value={customCalories}
                                    onChange={setCustomCalories}
                                />
                                <GoalSlider
                                    label="Protein"
                                    min={10}
                                    max={300}
                                    step={5}
                                    value={customProtein}
                                    onChange={setCustomProtein}
                                />
                                <div className="flex gap-2">
                                    <button
                                        onClick={handleSaveGoals}
                                        className="px-3 py-1 bg-green-600 text-white rounded text-sm"
                                    >
                                        Save
                                    </button>
                                    <button
                                        onClick={() => setEditingGoals(false)}
                                        className="px-3 py-1 bg-gray-300 rounded text-sm"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        )}

                        <ProgressBar label="Calories" summary={summary.calories} />
                        <ProgressBar label="Protein" summary={summary.protein} />
                        <HistoryTable items={summary.history || []} onDelete={handleDeleteEntry} />
                    </section>
                )}
            </div>
        </main>
    );
}