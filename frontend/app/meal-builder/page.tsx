/**
 * Meal Builder Page.
 *
 * Provides an interface for users to generate automated meal plans based on their
 * remaining daily calories and protein. Users can filter by dining hall and log 
 * entire suggested plans.
 *
 * @module app/meal-builder/page
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { ArrowLeft, RefreshCw, ChefHat, Info } from 'lucide-react';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

type MealPlanItem = {
    id: number;
    item: string;
    dining_hall: string;
    calories: number;
    protein: number;
    carbs?: number;
    fat?: number;
    availability?: string[];
    diet_types?: string[];
};

type MealPlan = {
    label: string;
    items: MealPlanItem[];
    totals: { 
        calories: number; 
        protein: number;
        carbs?: number;
        fat?: number;
    };
};

/**
 * The Meal Builder component.
 */
export default function MealBuilderPage() {
    const supabase = createClient();
    const router = useRouter();

    const [userId, setUserId] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
    const [logStatus, setLogStatus] = useState<string | null>(null);
    const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().slice(0, 10));
    const [logMealType, setLogMealType] = useState<string>('Lunch');
    const [selectedHall, setSelectedHall] = useState<string>('All');
    
    // Gap state
    const [remainingCalories, setRemainingCalories] = useState<number>(0);
    const [remainingProtein, setRemainingProtein] = useState<number>(0);
    const [remainingCarbs, setRemainingCarbs] = useState<number>(0);
    const [remainingFat, setRemainingFat] = useState<number>(0);

    // Initial load
    useEffect(() => {
        const checkAuth = async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error || !data.user) {
                router.push('/login');
                return;
            }
            setUserId(data.user.id);
            fetchDailySummary(data.user.id, selectedDate);
        };
        checkAuth();
    }, [router, supabase, selectedDate]);

    // Fetch gap
    const fetchDailySummary = async (uid: string, dateStr: string) => {
        try {
            const res = await fetch(`${BACKEND_URL}/api/users/${uid}/daily-summary?date=${dateStr}`);
            if (res.ok) {
                const data = await res.json();
                const remCal = Math.max((data.calories.target || 0) - (data.calories.total || 0), 0);
                const remPro = Math.max((data.protein.target || 0) - (data.protein.total || 0), 0);
                const remCarbs = Math.max((data.carbs?.target || 0) - (data.carbs?.total || 0), 0);
                const remFat = Math.max((data.fat?.target || 0) - (data.fat?.total || 0), 0);
                
                setRemainingCalories(remCal);
                setRemainingProtein(remPro);
                setRemainingCarbs(remCarbs);
                setRemainingFat(remFat);
                
                // Fetch plans once we have the gap
                fetchMealPlans(uid, dateStr, remCal, remPro, selectedHall);
            }
        } catch (e) {
            console.error("Failed to fetch summary", e);
        }
    };

    const fetchMealPlans = useCallback(async (uid: string, dateStr: string, calTarget: number, proTarget: number, hall: string) => {
        setLoading(true);
        setError(null);
        try {
            const diningHalls = hall === 'All' ? undefined : [hall];
            const res = await fetch(`${BACKEND_URL}/api/meal-builder/suggest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: uid,
                    date: dateStr,
                    calorie_target: calTarget,
                    protein_target: proTarget,
                    dining_halls: diningHalls,
                    max_items: 4,
                }),
            });

            if (!res.ok) {
                throw new Error(`Failed to build meal plan (status ${res.status})`);
            }

            const json = await res.json();
            setMealPlans(json.meals || []);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to build meal plan';
            setError(message);
        } finally {
            setLoading(false);
        }
    }, []);

    const handleRefresh = () => {
        if (userId) {
            fetchMealPlans(userId, selectedDate, remainingCalories, remainingProtein, selectedHall);
        }
    };

    const handleLogPlan = async (plan: MealPlan) => {
        if (!userId) return;
        setLogStatus(null);
        setError(null);

        try {
            for (const item of plan.items) {
                await fetch(`${BACKEND_URL}/api/users/${userId}/log-food`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        item_name: item.item,
                        meal_type: logMealType.toLowerCase(),
                        calories: item.calories,
                        protein: item.protein,
                        date: selectedDate,
                    }),
                });
            }
            setLogStatus(`Logged meal: ${plan.label}`);
            // Refresh gap after logging
            fetchDailySummary(userId, selectedDate);
        } catch (err: unknown) {
            console.error(err);
            setError('Failed to log meal');
        }
    };

    return (
        <main className="max-w-5xl mx-auto p-4 lg:p-8 space-y-6">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <button 
                        onClick={() => router.push('/dashboard')}
                        className="p-2 rounded-full hover:bg-gray-100 text-gray-500 transition-colors"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Meal Builder</h1>
                        <p className="text-gray-600">Smart recommendations to hit your targets.</p>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Sidebar: Controls & Gap */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 space-y-4">
                        <h3 className="font-semibold text-gray-900">Plan Settings</h3>
                        
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700">Date</label>
                            <input 
                                type="date" 
                                value={selectedDate} 
                                onChange={(e) => setSelectedDate(e.target.value)} 
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700">Log As</label>
                            <select 
                                value={logMealType} 
                                onChange={(e) => setLogMealType(e.target.value)} 
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            >
                                <option>Breakfast</option>
                                <option>Lunch</option>
                                <option>Dinner</option>
                                <option>Snack</option>
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700">Dining Hall</label>
                            <select 
                                value={selectedHall} 
                                onChange={(e) => setSelectedHall(e.target.value)} 
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            >
                                <option value="All">All Halls</option>
                                <option value="Worcester">Worcester</option>
                                <option value="Franklin">Franklin</option>
                                <option value="Hampshire">Hampshire</option>
                                <option value="Berkshire">Berkshire</option>
                            </select>
                        </div>

                        <div className="pt-4 border-t border-gray-100">
                            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Current Gap</p>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Calories Needed</span>
                                    <span className="font-bold text-gray-900">{Math.round(remainingCalories)}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Protein Needed</span>
                                    <span className="font-bold text-gray-900">{Math.round(remainingProtein)}g</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Carbs Needed</span>
                                    <span className="font-bold text-gray-900">{Math.round(remainingCarbs)}g</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Fat Needed</span>
                                    <span className="font-bold text-gray-900">{Math.round(remainingFat)}g</span>
                                </div>
                            </div>
                        </div>

                        <button 
                            onClick={handleRefresh}
                            className="w-full py-2 flex items-center justify-center gap-2 rounded-lg border border-gray-300 hover:bg-gray-50 text-sm font-medium transition-colors"
                        >
                            <RefreshCw className="w-4 h-4" /> Refresh Options
                        </button>
                    </div>

                    {logStatus && (
                        <div className="p-4 bg-green-50 text-green-700 rounded-xl border border-green-200 text-sm flex items-center gap-2">
                            ✅ {logStatus}
                        </div>
                    )}
                </div>

                {/* Main Content: Plans */}
                <div className="md:col-span-2 space-y-6">
                    {loading && (
                        <div className="text-center py-12 bg-white rounded-xl border border-gray-100">
                            <p className="text-gray-500 animate-pulse">Analyzing menu data...</p>
                        </div>
                    )}

                    {error && (
                        <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-200 text-sm">
                            ⚠️ {error}
                        </div>
                    )}

                    {!loading && !error && mealPlans.length === 0 && (
                        <div className="text-center py-12 bg-white rounded-xl border border-dashed border-gray-300">
                            <ChefHat className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                            <p className="text-gray-500">No suggestions found. Try adjusting your targets or filters.</p>
                        </div>
                    )}

                    {!loading && mealPlans.map((plan, idx) => (
                        <div key={idx} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:border-[#881C1B]/30 transition-all">
                            <div className="p-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
                                <div>
                                    <h3 className="font-bold text-gray-900">{plan.label}</h3>
                                    <div className="flex gap-3 text-sm mt-1">
                                        <span className="text-gray-600">
                                            <span className="font-semibold text-gray-900">{Math.round(plan.totals.calories)}</span> kcal
                                        </span>
                                        <span className="text-gray-600">
                                            <span className="font-semibold text-gray-900">{Math.round(plan.totals.protein)}g</span> protein
                                        </span>
                                        {plan.totals.carbs !== undefined && (
                                            <span className="text-gray-600">
                                                <span className="font-semibold text-gray-900">{Math.round(plan.totals.carbs)}g</span> carb
                                            </span>
                                        )}
                                        {plan.totals.fat !== undefined && (
                                            <span className="text-gray-600">
                                                <span className="font-semibold text-gray-900">{Math.round(plan.totals.fat)}g</span> fat
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <button 
                                    onClick={() => handleLogPlan(plan)}
                                    className="px-4 py-2 bg-[#881C1B] text-white rounded-lg text-sm font-medium hover:bg-[#6d1615] shadow-sm"
                                >
                                    Log Meal
                                </button>
                            </div>
                            <div className="divide-y divide-gray-100">
                                {plan.items.map((item) => (
                                    <div key={item.id} className="p-4 flex justify-between items-start gap-4">
                                        <div>
                                            <p className="font-medium text-gray-900">{item.item}</p>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 text-[10px] uppercase tracking-wide border border-gray-200">
                                                    {item.dining_hall}
                                                </span>
                                                {item.diet_types?.slice(0, 2).map(dt => (
                                                    <span key={dt} className="text-[10px] text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
                                                        {dt}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="text-right text-sm text-gray-600 shrink-0">
                                            <p>{Math.round(item.calories)} kcal</p>
                                            <p>{Math.round(item.protein)}g pro</p>
                                            {(item.carbs !== undefined || item.fat !== undefined) && (
                                                <p className="text-xs text-gray-400 mt-0.5">
                                                    {item.carbs ? Math.round(item.carbs) : 0}c • {item.fat ? Math.round(item.fat) : 0}f
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                    
                    {!loading && mealPlans.length > 0 && (
                        <div className="flex gap-2 items-start p-4 bg-blue-50 text-blue-700 rounded-xl text-sm">
                            <Info className="w-5 h-5 shrink-0" />
                            <p>These suggestions are generated based on your remaining daily targets. Logging a meal will update your progress and gap analysis automatically.</p>
                        </div>
                    )}
                </div>
            </div>
        </main>
    );
}