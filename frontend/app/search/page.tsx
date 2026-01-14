/**
 * Search Page.
 *
 * A dedicated interface for filtering and searching the food database using
 * structured criteria (dining hall, meal, diet, calories).
 *
 * @module app/search/page
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

// Types for our API data
interface FilterOptions {
    dining_halls: string[];
    meals: string[];
    diets: string[];
}

interface FoodItem {
    item: string;
    dining_hall: string;
    calories: number | null;
    availability_today: string[] | null;
    diet_types: string[] | null;
    allergens: string[] | null;
}

export default function SearchPage() {
    const supabase = createClient();
    const router = useRouter();

    // State for filter options (from backend)
    const [options, setOptions] = useState<FilterOptions | null>(null);

    // State for user selections
    const [selectedHall, setSelectedHall] = useState<string>('');
    const [selectedMeal, setSelectedMeal] = useState<string>('');
    const [selectedDiet, setSelectedDiet] = useState<string>('');
    const [minCal, setMinCal] = useState<string>('');
    const [maxCal, setMaxCal] = useState<string>('');

    // State for results
    const [results, setResults] = useState<FoodItem[]>([]);
    const [loading, setLoading] = useState(false);

    // 1. Fetch Filter Options on Mount
    useEffect(() => {
        async function fetchOptions() {
            try {
                const res = await fetch('http://localhost:8000/api/food/options');
                if (res.ok) {
                    const data = await res.json();
                    setOptions(data);
                }
            } catch (err) {
                console.error("Failed to fetch options", err);
            }
        }
        fetchOptions();
    }, []);

    // 2. Search Function
    const handleSearch = async () => {
        setLoading(true);
        try {
            // Build Query Params
            const params = new URLSearchParams();
            if (selectedHall) params.append('dining_hall', selectedHall);
            if (selectedMeal) params.append('meal', selectedMeal);
            if (selectedDiet) params.append('diets', selectedDiet);
            if (minCal) params.append('min_calories', minCal);
            if (maxCal) params.append('max_calories', maxCal);

            const res = await fetch(`http://localhost:8000/api/food/search?${params.toString()}`);
            if (res.ok) {
                const data = await res.json();
                setResults(data);
            }
        } catch (err) {
            console.error("Search failed", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <h1 className="text-3xl font-bold text-gray-900">Food Search</h1>
                    <Button variant="outline" onClick={() => router.push('/chat')}>Back to Chat</Button>
                </div>

                {/* Filters Section */}
                <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        
                        {/* Dining Hall Select */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Dining Hall</label>
                            <select 
                                className="w-full p-2 border rounded-md"
                                value={selectedHall}
                                onChange={(e) => setSelectedHall(e.target.value)}
                            >
                                <option value="">Any</option>
                                {options?.dining_halls.map(hall => (
                                    <option key={hall} value={hall}>{hall}</option>
                                ))}
                            </select>
                        </div>

                        {/* Meal Select */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Meal</label>
                            <select 
                                className="w-full p-2 border rounded-md"
                                value={selectedMeal}
                                onChange={(e) => setSelectedMeal(e.target.value)}
                            >
                                <option value="">Any</option>
                                {options?.meals.map(meal => (
                                    <option key={meal} value={meal}>{meal}</option>
                                ))}
                            </select>
                        </div>

                        {/* Diet Select */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Diet</label>
                            <select 
                                className="w-full p-2 border rounded-md"
                                value={selectedDiet}
                                onChange={(e) => setSelectedDiet(e.target.value)}
                            >
                                <option value="">Any</option>
                                {options?.diets.map(diet => (
                                    <option key={diet} value={diet}>{diet}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Calorie Range */}
                    <div className="grid grid-cols-2 gap-4 max-w-sm">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Min Cals</label>
                            <input 
                                type="number" 
                                className="w-full p-2 border rounded-md"
                                placeholder="0"
                                value={minCal}
                                onChange={(e) => setMinCal(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Max Cals</label>
                            <input 
                                type="number" 
                                className="w-full p-2 border rounded-md"
                                placeholder="2000"
                                value={maxCal}
                                onChange={(e) => setMaxCal(e.target.value)}
                            />
                        </div>
                    </div>

                    <Button 
                        onClick={handleSearch} 
                        className="bg-[#881C1B] hover:bg-[#6d1615] text-white w-full md:w-auto"
                        disabled={loading}
                    >
                        {loading ? 'Searching...' : 'Find Food'}
                    </Button>
                </div>

                {/* Results Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {results.map((item, idx) => (
                        <Card key={idx} className="hover:shadow-md transition-shadow">
                            <CardHeader className="pb-2">
                                <div className="flex justify-between items-start">
                                    <CardTitle className="text-lg font-bold text-gray-900">{item.item}</CardTitle>
                                    <Badge variant="outline">{item.dining_hall}</Badge>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-2 text-sm text-gray-600">
                                    <div className="flex justify-between">
                                        <span>Calories:</span>
                                        <span className="font-semibold">{item.calories || 'N/A'}</span>
                                    </div>
                                    <div>
                                        <span className="font-semibold block mb-1">Available for:</span>
                                        <div className="flex flex-wrap gap-1">
                                            {item.availability_today?.map(meal => (
                                                <Badge key={meal} className="bg-gray-100 text-gray-800 hover:bg-gray-200">
                                                    {meal}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                    {item.diet_types && item.diet_types.length > 0 && (
                                        <div>
                                            <span className="font-semibold block mb-1">Diets:</span>
                                            <div className="flex flex-wrap gap-1">
                                                {item.diet_types.map(diet => (
                                                    <span key={diet} className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">
                                                        {diet}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>

                {!loading && results.length === 0 && (
                    <p className="text-center text-gray-500 mt-10">No items found. Try adjusting your filters.</p>
                )}
            </div>
        </main>
    );
}