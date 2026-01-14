/**
 * Food Logging Page.
 *
 * Allows users to search the dining database or manually enter custom food items
 * to add to their daily nutritional log. It also displays a sidebar summary of
 * the current day's intake.
 *
 * @module app/dashboard/log/page
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { Filter, X, ChevronDown, ChevronUp, Calendar, ArrowLeft, PlusCircle } from 'lucide-react';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type FoodResult = {
    id: number;
    item: string;
    dining_hall: string;
    calories: number | null;
    protein_g: number | null;
    availability_today: string[] | null;
    diet_types: string[] | null;
    allergens: string[] | null;
};

type LogEntry = {
    id: number;
    item: string;
    calories: number;
    protein_g: number;
    mealtime: string;
};

type FilterOptions = {
    dining_halls: string[];
    meals: string[];
    diets: string[];
};

const mealOptions = ['Breakfast', 'Lunch', 'Dinner', "Grab' n Go", 'Late Night'] as const;

/**
 * Main component for the Food Log page.
 */
export default function FoodLogPage() {
    const supabase = createClient();
    const router = useRouter();

    const [userId, setUserId] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [logStatus, setLogStatus] = useState<string | null>(null);
    
    // View State (Search is default)
    const [viewMode, setViewMode] = useState<'search' | 'custom'>('search');

    // Data State
    const [searchTerm, setSearchTerm] = useState('');
    const [results, setResults] = useState<FoodResult[]>([]);
    const [dailyLog, setDailyLog] = useState<LogEntry[]>([]);
    
    // Custom Entry Form State
    const [customName, setCustomName] = useState('');
    const [customCals, setCustomCals] = useState('');
    const [customProtein, setCustomProtein] = useState('');

    // Filter State
    const [showFilters, setShowFilters] = useState(false);
    const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
    const [selectedHall, setSelectedHall] = useState('');
    const [selectedMealFilter, setSelectedMealFilter] = useState('');
    const [selectedDiet, setSelectedDiet] = useState('');
    const [minCal, setMinCal] = useState('');
    const [maxCal, setMaxCal] = useState('');

    // Log Control State (Global)
    const [mealType, setMealType] = useState<string>('Dinner');
    const [logDate, setLogDate] = useState<string>(new Date().toISOString().slice(0, 10));

    // Totals
    const totalCalories = dailyLog.reduce((sum, entry) => sum + (entry.calories || 0), 0);
    const totalProtein = dailyLog.reduce((sum, entry) => sum + (entry.protein_g || 0), 0);

    // 1. Auth & Data Fetch
    useEffect(() => {
        const checkUser = async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error || !data.user) {
                router.push('/login');
                return;
            }
            setUserId(data.user.id);
            fetchFilterOptions();
            fetchDailyLog(data.user.id, logDate);
        };
        checkUser();
    }, [router, supabase, logDate]);

    const fetchFilterOptions = async () => {
        try {
            const res = await fetch(`${BACKEND_URL}/api/food/options`);
            if (res.ok) setFilterOptions(await res.json());
        } catch (e) {
            console.error("Failed to load options", e);
        }
    };

    const fetchDailyLog = async (uid: string, dateStr: string) => {
        try {
            const res = await fetch(`${BACKEND_URL}/api/users/${uid}/log?date_str=${dateStr}`);
            if (res.ok) {
                setDailyLog(await res.json());
            }
        } catch (e) {
            console.error("Failed to fetch log", e);
        }
    };

    // 2. Search Logic
    const handleSearch = async (e?: React.FormEvent) => {
        e?.preventDefault();
        setLoading(true);
        setError(null);
        setLogStatus(null);

        try {
            const params = new URLSearchParams();
            if (searchTerm.trim()) params.append('q', searchTerm);
            if (selectedHall) params.append('dining_hall', selectedHall);
            if (selectedMealFilter) params.append('meal', selectedMealFilter);
            if (selectedDiet) params.append('diets', selectedDiet);
            if (minCal) params.append('min_calories', minCal);
            if (maxCal) params.append('max_calories', maxCal);
            
            params.append('limit', '50');

            const res = await fetch(`${BACKEND_URL}/api/food/search?${params.toString()}`);
            if (!res.ok) throw new Error(await res.text());
            
            const data = await res.json();
            setResults(Array.isArray(data) ? data : data.results || []);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Search failed';
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    // 3. Log Handler (Database Items)
    const handleLog = async (item: FoodResult) => {
        if (!userId) return;
        setLogStatus(null);
        setError(null);
        try {
            const payload = {
                item_name: item.item,
                calories: item.calories ?? 0,
                protein: item.protein_g ?? 0,
                meal_type: mealType.toLowerCase(),
                date: logDate,
            };
            const res = await fetch(`${BACKEND_URL}/api/users/${userId}/log-food`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error(await res.text());
            
            setLogStatus(`Logged ${item.item}`);
            fetchDailyLog(userId, logDate);
        } catch (err: unknown) {
            console.error(err);
            setError('Failed to log food');
        }
    };

    // 4. Log Handler (Custom Items)
    const handleCustomLog = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!userId || !customName || !customCals) {
            setError("Please fill in Name and Calories.");
            return;
        }
        
        try {
            const payload = {
                item_name: customName,
                calories: parseFloat(customCals),
                protein: customProtein ? parseFloat(customProtein) : 0,
                meal_type: mealType.toLowerCase(),
                date: logDate,
            };
            
            const res = await fetch(`${BACKEND_URL}/api/users/${userId}/log-food`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            
            if (!res.ok) throw new Error(await res.text());

            setLogStatus(`Logged custom item: ${customName}`);
            // Reset form and go back to search
            setCustomName('');
            setCustomCals('');
            setCustomProtein('');
            setViewMode('search');
            
            fetchDailyLog(userId, logDate);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to log custom item';
            setError(message);
        }
    };

    const clearFilters = () => {
        setSelectedHall('');
        setSelectedMealFilter('');
        setSelectedDiet('');
        setMinCal('');
        setMaxCal('');
    };

    return (
        <main className="max-w-7xl mx-auto p-4 lg:p-8 space-y-6">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Food Log</h1>
                    <p className="text-gray-600">Track your meals from UMass Dining.</p>
                </div>
                <button onClick={() => router.push('/chat')} className="px-4 py-2 rounded-md bg-[#881C1B] text-white hover:bg-[#6d1615] self-start md:self-auto">
                    Back to Chat
                </button>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* --- LEFT COLUMN: Search & Entry --- */}
                <div className="lg:col-span-2 space-y-6">
                    
                    {/* Global Log Settings (Meal & Date) */}
                    <div className="flex flex-wrap gap-4 items-center bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-gray-700">Log As:</span>
                            <select 
                                value={mealType} 
                                onChange={(e) => setMealType(e.target.value)} 
                                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm bg-white cursor-pointer hover:border-[#881C1B] focus:ring-[#881C1B]"
                            >
                                {mealOptions.map((m) => <option key={m} value={m}>{m}</option>)}
                            </select>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-gray-700">Date:</span>
                            <input 
                                type="date" 
                                value={logDate} 
                                onChange={(e) => setLogDate(e.target.value)} 
                                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm bg-white cursor-pointer hover:border-[#881C1B]" 
                            />
                        </div>
                    </div>

                    {/* Messages */}
                    {logStatus && <div className="p-3 bg-green-50 text-green-700 rounded-lg text-sm border border-green-200 flex items-center gap-2">✅ {logStatus}</div>}
                    {error && <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm border border-red-200">⚠️ {error}</div>}

                    {/* === VIEW 1: SEARCH DATABASE === */}
                    {viewMode === 'search' && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-left-2 duration-300">
                            {/* Search Box */}
                            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 space-y-4">
                                <form onSubmit={handleSearch} className="space-y-4">
                                    <div className="flex flex-col md:flex-row gap-2">
                                        <input
                                            type="text"
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            placeholder="Search food (e.g., 'chicken')"
                                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#881C1B] focus:border-transparent outline-none transition-all"
                                        />
                                        
                                        <select 
                                            value={selectedHall} 
                                            onChange={(e) => setSelectedHall(e.target.value)} 
                                            className="md:w-48 px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-[#881C1B] outline-none"
                                        >
                                            <option value="">All Dining Halls</option>
                                            {filterOptions?.dining_halls.map(h => <option key={h} value={h}>{h}</option>)}
                                        </select>

                                        <button 
                                            type="button" 
                                            onClick={() => setShowFilters(!showFilters)}
                                            className={`px-3 py-2 rounded-lg border flex items-center gap-2 transition-colors ${showFilters ? 'bg-gray-100 border-gray-400' : 'border-gray-300 hover:bg-gray-50'}`}
                                        >
                                            <Filter className="w-4 h-4" />
                                        </button>
                                        <button type="submit" disabled={loading} className="px-6 py-2 rounded-lg bg-[#881C1B] text-white hover:bg-[#6d1615] disabled:opacity-50 font-medium transition-colors shadow-sm">
                                            {loading ? '...' : 'Search'}
                                        </button>
                                    </div>

                                    {/* Advanced Filters */}
                                    {showFilters && (
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-100 animate-in fade-in slide-in-from-top-1">
                                            <div className="space-y-1">
                                                <label className="text-xs font-semibold text-gray-500 uppercase">Meal Period</label>
                                                <select value={selectedMealFilter} onChange={(e) => setSelectedMealFilter(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md text-sm">
                                                    <option value="">Any</option>
                                                    {filterOptions?.meals.map(m => <option key={m} value={m}>{m}</option>)}
                                                </select>
                                            </div>
                                            <div className="space-y-1">
                                                <label className="text-xs font-semibold text-gray-500 uppercase">Diet</label>
                                                <select value={selectedDiet} onChange={(e) => setSelectedDiet(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md text-sm">
                                                    <option value="">Any</option>
                                                    {filterOptions?.diets.map(d => <option key={d} value={d}>{d}</option>)}
                                                </select>
                                            </div>
                                            <div className="space-y-1">
                                                <label className="text-xs font-semibold text-gray-500 uppercase">Min Calories</label>
                                                <input type="number" value={minCal} onChange={(e) => setMinCal(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md text-sm" placeholder="0" />
                                            </div>
                                            <div className="space-y-1">
                                                <label className="text-xs font-semibold text-gray-500 uppercase">Max Calories</label>
                                                <input type="number" value={maxCal} onChange={(e) => setMaxCal(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md text-sm" placeholder="2000" />
                                            </div>
                                            <div className="md:col-span-2 flex justify-end">
                                                <button type="button" onClick={clearFilters} className="text-sm text-gray-500 hover:text-gray-800 flex items-center gap-1">
                                                    <X className="w-3 h-3" /> Clear Filters
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </form>
                            </div>

                            {/* Search Results */}
                            <section className="space-y-4">
                                {results.length === 0 ? (
                                    <div className="text-center py-10 border-2 border-dashed border-gray-200 rounded-xl bg-gray-50/50">
                                        <p className="text-gray-500 mb-4">No results found.</p>
                                    </div>
                                ) : (
                                    <div className="grid gap-3">
                                        {results.map((item) => (
                                            <div key={item.id} className="group border border-gray-200 rounded-xl p-4 bg-white hover:border-[#881C1B]/30 hover:shadow-md transition-all">
                                                <div className="flex justify-between items-start gap-4">
                                                    <div>
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <h3 className="font-bold text-gray-900">{item.item}</h3>
                                                            <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 text-[10px] border border-gray-200 uppercase tracking-wide">
                                                                {item.dining_hall}
                                                            </span>
                                                        </div>
                                                        <div className="text-sm text-gray-600 flex items-center gap-3">
                                                            <span className="font-medium text-gray-900">{item.calories ? Math.round(item.calories) : '-'} kcal</span>
                                                            <span className="text-gray-400">|</span>
                                                            <span>{item.protein_g ? Math.round(item.protein_g) : '0'}g protein</span>
                                                        </div>
                                                        {item.diet_types && item.diet_types.length > 0 && (
                                                            <div className="flex flex-wrap gap-1 mt-2">
                                                                {item.diet_types.map(diet => (
                                                                    <span key={diet} className="text-[10px] font-bold text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
                                                                        {diet}
                                                                    </span>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                    <button 
                                                        onClick={() => handleLog(item)} 
                                                        className="shrink-0 px-4 py-2 rounded-lg bg-gray-900 text-white hover:bg-[#881C1B] text-sm font-medium transition-colors"
                                                    >
                                                        Log
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* --- CUSTOM ENTRY TRIGGER BUTTON --- */}
                                <div className="flex justify-center pt-4">
                                    <button 
                                        onClick={() => setViewMode('custom')}
                                        className="flex items-center gap-2 px-6 py-3 rounded-full bg-white border-2 border-gray-200 text-gray-600 font-medium hover:border-[#881C1B] hover:text-[#881C1B] transition-all shadow-sm group"
                                    >
                                        <PlusCircle className="w-5 h-5 group-hover:scale-110 transition-transform" />
                                        Can't find it? Add Custom Food
                                    </button>
                                </div>
                            </section>
                        </div>
                    )}

                    {/* === VIEW 2: CUSTOM ENTRY FORM === */}
                    {viewMode === 'custom' && (
                        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-200 animate-in fade-in zoom-in-95 duration-200">
                            <div className="flex items-center gap-4 mb-6 pb-4 border-b border-gray-100">
                                <button 
                                    onClick={() => setViewMode('search')}
                                    className="p-2 rounded-full hover:bg-gray-100 text-gray-500 transition-colors"
                                >
                                    <ArrowLeft className="w-5 h-5" />
                                </button>
                                <h2 className="text-xl font-bold text-gray-900">Add Custom Item</h2>
                            </div>

                            <form onSubmit={handleCustomLog} className="space-y-6 max-w-lg mx-auto">
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-2">Item Name <span className="text-red-500">*</span></label>
                                    <input 
                                        type="text" 
                                        value={customName}
                                        onChange={(e) => setCustomName(e.target.value)}
                                        placeholder="e.g. Homemade Sandwich" 
                                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#881C1B] focus:border-transparent outline-none transition-all bg-gray-50 focus:bg-white"
                                        required
                                    />
                                </div>
                                
                                <div className="grid grid-cols-2 gap-6">
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-2">Calories <span className="text-red-500">*</span></label>
                                        <div className="relative">
                                            <input 
                                                type="number" 
                                                value={customCals}
                                                onChange={(e) => setCustomCals(e.target.value)}
                                                placeholder="0" 
                                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#881C1B] focus:border-transparent outline-none transition-all bg-gray-50 focus:bg-white"
                                                required
                                            />
                                            <span className="absolute right-4 top-3 text-gray-400 text-sm">kcal</span>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-2">Protein (Optional)</label>
                                        <div className="relative">
                                            <input 
                                                type="number" 
                                                value={customProtein}
                                                onChange={(e) => setCustomProtein(e.target.value)}
                                                placeholder="0" 
                                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#881C1B] focus:border-transparent outline-none transition-all bg-gray-50 focus:bg-white"
                                            />
                                            <span className="absolute right-4 top-3 text-gray-400 text-sm">g</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 flex gap-3">
                                    <button 
                                        type="button"
                                        onClick={() => setViewMode('search')}
                                        className="flex-1 px-6 py-3 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button 
                                        type="submit" 
                                        className="flex-[2] px-6 py-3 rounded-lg bg-[#881C1B] text-white font-medium hover:bg-[#6d1615] shadow-md hover:shadow-lg transition-all"
                                    >
                                        Add to Log
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}
                </div>

                {/* --- RIGHT COLUMN: Daily Log Sidebar --- */}
                <div className="lg:col-span-1">
                    <div className="sticky top-6 space-y-6">
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
                            <div className="bg-[#881C1B] p-4 text-white">
                                <h2 className="font-bold text-lg flex items-center gap-2">
                                    <Calendar className="w-5 h-5" /> Today's Summary
                                </h2>
                                <p className="text-white/80 text-sm">{logDate}</p>
                            </div>
                            
                            <div className="p-6 text-center border-b border-gray-100">
                                <div className="text-5xl font-extrabold text-gray-900">{Math.round(totalCalories)}</div>
                                <div className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-1">Calories</div>
                                
                                <div className="mt-4 pt-4 border-t border-gray-100 flex justify-center gap-6">
                                    <div>
                                        <div className="text-xl font-bold text-gray-700">{Math.round(totalProtein)}g</div>
                                        <div className="text-[10px] text-gray-400 uppercase">Protein</div>
                                    </div>
                                </div>
                            </div>

                            <div className="p-4 bg-gray-50 max-h-[500px] overflow-y-auto space-y-2">
                                {dailyLog.length === 0 ? (
                                    <p className="text-center text-sm text-gray-400 py-4 italic">No items logged today.</p>
                                ) : (
                                    dailyLog.map((log) => (
                                        <div key={log.id} className="bg-white p-3 rounded-lg border border-gray-200 shadow-sm flex justify-between items-center group">
                                            <div className="overflow-hidden">
                                                <p className="font-medium text-gray-800 text-sm truncate">{log.item}</p>
                                                <p className="text-xs text-gray-500 capitalize">{log.mealtime}</p>
                                            </div>
                                            <div className="text-right pl-2 shrink-0">
                                                <p className="font-bold text-gray-900 text-sm">{Math.round(log.calories)}</p>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}