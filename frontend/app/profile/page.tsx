/**
 * User Profile Page.
 *
 * Allows users to view and edit their dietary settings, including allergies,
 * constraints, and health goals. Syncs data with the backend.
 *
 * @module app/profile/page
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

interface ConstraintDTO {
    constraint: string;
    constraint_type: string;
}

// --- Reusable UI Components (Same as Onboarding) ---
const Checkbox = ({ label, isChecked, onChange }: { label: string; isChecked: boolean; onChange: () => void }) => (
    <label className="flex items-center space-x-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all cursor-pointer bg-white">
        <input type="checkbox" checked={isChecked} onChange={onChange} className="h-5 w-5 rounded border-gray-300 text-[#881C1B] focus:ring-[#881C1B]" />
        <span className="text-gray-800">{label}</span>
    </label>
);

const SelectableCard = ({ title, isSelected, onClick }: { title: string; isSelected: boolean; onClick: () => void }) => (
    <button
        type="button"
        onClick={onClick}
        className={`flex-1 min-w-[150px] p-4 rounded-lg border-2 text-center transition-all ${
            isSelected ? 'border-[#881C1B] bg-[#fff6f6]' : 'border-gray-200 bg-white hover:border-gray-300'
        }`}
    >
        <span className={`font-semibold ${isSelected ? 'text-[#881C1B]' : 'text-gray-800'}`}>{title}</span>
    </button>
);

const SelectableTag = ({ label, isSelected, onClick }: { label: string; isSelected: boolean; onClick: () => void }) => (
    <button
        type="button"
        onClick={onClick}
        className={`px-4 py-2 rounded-full border transition-all text-sm ${
            isSelected ? 'bg-[#881C1B] text-white border-[#881C1B]' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'
        }`}
    >
        {label}
    </button>
);

const DIET_OPTIONS = ['Vegan', 'Vegetarian', 'Halal', 'Kosher'];
const GOAL_OPTIONS = ['Lose Weight', 'Maintain Weight', 'Gain Muscle / Weight', 'Just Exploring'];
const CUISINE_OPTIONS = ['Mediterranean', 'East Asian', 'Tandoori / South Asian', 'Mexican / Latin American', 'Italian (Pizza, Pasta)', 'American Comfort', 'Salads & Sandwiches'];

/**
 * ProfilePage displays the authenticated user's saved dietary profile.
 *
 * Fetches the profile from the backend; if not found redirects to onboarding.
 * Provides logout and navigation back to chat.
 */
export default function ProfilePage() {
    /**
     * State:
     * - loading: Indicates initial fetch in progress.
     * - userEmail: Email derived from Supabase auth session.
     * - diets: List of diet preference strings.
     * - allergies: List of allergy constraint strings.
     * - goal: User's nutrition/health goal string or null.
     * - error: Error message if profile fetch fails.
     */
    const supabase = createClient();
    const router = useRouter();

    const [loading, setLoading] = useState(true);
    const [userEmail, setUserEmail] = useState<string>('');
    const [goal, setGoal] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [userId, setUserId] = useState<string>('');

    // form data states
    const [allergiesInput, setAllergiesInput] = useState(''); // String for input field
    const [cuisines, setCuisines] = useState<string[]>([]);
    const [dislikes, setDislikes] = useState('');
    const [diets, setDiets] = useState<string[]>([]);

    useEffect(() => {
        const loadProfile = async () => {
            try {
                const { data, error } = await supabase.auth.getUser();
                if (error) {
                    router.push('/');
                    return;
                }
                if (!data.user) {
                    router.push('/');
                    return;
                }
                setUserEmail(data.user.email || '');
                setUserId(data.user.id);

                const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/profile/${data.user.id}`);
                if (resp.status === 404) {
                    router.push('/onboarding');
                    return;
                }
                if (!resp.ok) {
                    setError(`Failed to load profile (status ${resp.status})`);
                    return;
                }
                const json = await resp.json();
                const constraints: ConstraintDTO[] = json.dietary_constraints || [];
                setDiets(constraints.filter((c) => c.constraint_type === 'preference').map((c) => c.constraint));
                const allergyList = constraints.filter((c) => c.constraint_type === 'allergy').map((c) => c.constraint);
                setAllergiesInput(allergyList.join(', '));
                setGoal(json.goal || null);
                setDislikes(json.dislikes || '');
                setCuisines(json.liked_cuisines || []);
            } catch {
                setError('Unexpected error loading profile');
            } finally {
                setLoading(false);
            }
        };
        loadProfile();
    }, [supabase, router]);

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.push('/');
    };


    const toggleItem = (list: string[], setter: (list: string[]) => void, item: string) => {
        if (list.includes(item)) {
            setter(list.filter((i) => i !== item));
        } else {
            setter([...list, item]);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        setError(null);
    
        try {
            if (!userId) {
                throw new Error('User ID missing. Please refresh.');
            }
    
            const allergyList = allergiesInput
                .split(',')
                .map((s) => s.trim())
                .filter((s) => s.length > 0);
    
            const payload = {
                user_id: userId,
                email: userEmail || '',
                diets: diets,
                allergies: allergyList,
                goal: goal,
                dislikes: dislikes,
                liked_cuisines: cuisines, 
            };
    
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/profile`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
    
            if (!response.ok) {
                throw new Error('Failed to update profile');
            }
    
            setIsEditing(false);
        } catch (err) {
            console.error(err);
            setError('Failed to save changes.');
        } finally {
            setIsSaving(false);
        }
    };

    if (loading) {
        return (
            <main className="flex items-center justify-center h-screen bg-gray-50">
                <p className="text-gray-600">Loading...</p>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-2xl mx-auto bg-white shadow-sm rounded-lg p-6 space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-white">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Your Profile</h1>
                        <p className="text-gray-500 text-sm">{userEmail}</p>
                    </div>
                    <div className="flex gap-3">
                        {!isEditing && (
                            <button 
                                onClick={() => setIsEditing(true)} 
                                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                            >
                                Edit Profile
                            </button>
                        )}
                        <button 
                            onClick={handleLogout} 
                            className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100 transition-colors"
                        >
                            Log Out
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="m-6 p-4 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm">
                        {error}
                    </div>
                )}

                <div className="p-6 md:p-8 space-y-8">
                    
                    {/* --- GOALS --- */}
                    <section>
                        <h2 className="text-lg font-bold text-gray-900 mb-4">Health Goal</h2>
                        {isEditing ? (
                            <div className="flex flex-wrap gap-3">
                                {GOAL_OPTIONS.map((item) => (
                                    <SelectableCard key={item} title={item} isSelected={goal === item} onClick={() => setGoal(item)} />
                                ))}
                            </div>
                        ) : (
                            <div className="p-4 bg-gray-50 rounded-lg border border-gray-100 text-gray-800 font-medium">
                                {goal || 'No goal selected'}
                            </div>
                        )}
                    </section>

                    <hr className="border-gray-100" />

                    {/* --- DIETS --- */}
                    <section>
                        <h2 className="text-lg font-bold text-gray-900 mb-4">Dietary Preferences</h2>
                        {isEditing ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {DIET_OPTIONS.map((item) => (
                                    <Checkbox key={item} label={item} isChecked={diets.includes(item)} onChange={() => toggleItem(diets, setDiets, item)} />
                                ))}
                            </div>
                        ) : (
                            <div className="flex flex-wrap gap-2">
                                {diets.length > 0 ? diets.map(d => (
                                    <span key={d} className="px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm font-medium border border-green-100">
                                        {d}
                                    </span>
                                )) : <p className="text-gray-500 italic">No specific diets</p>}
                            </div>
                        )}
                    </section>

                    {/* --- ALLERGIES --- */}
                    <section>
                        <h2 className="text-lg font-bold text-gray-900 mb-4">Allergies & Intolerances</h2>
                        {isEditing ? (
                            <input
                                type="text"
                                value={allergiesInput}
                                onChange={(e) => setAllergiesInput(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#881C1B] focus:border-transparent transition-all"
                                placeholder="e.g., Peanuts, Dairy, Gluten (Comma separated)"
                            />
                        ) : (
                            <div className="text-gray-800">
                                {allergiesInput ? (
                                    <div className="flex flex-wrap gap-2">
                                        {allergiesInput.split(',').map((a, i) => (
                                            <span key={i} className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm font-medium border border-red-100">
                                                {a.trim()}
                                            </span>
                                        ))}
                                    </div>
                                ) : <p className="text-gray-500 italic">No allergies listed</p>}
                            </div>
                        )}
                    </section>

                    <hr className="border-gray-100" />

                    {/* --- CUISINES --- */}
                    <section>
                        <h2 className="text-lg font-bold text-gray-900 mb-4">Liked Cuisines</h2>
                        {isEditing ? (
                            <div className="flex flex-wrap gap-2">
                                {CUISINE_OPTIONS.map((item) => (
                                    <SelectableTag key={item} label={item} isSelected={cuisines.includes(item)} onClick={() => toggleItem(cuisines, setCuisines, item)} />
                                ))}
                            </div>
                        ) : (
                            <div className="flex flex-wrap gap-2">
                                {cuisines.length > 0 ? cuisines.map(c => (
                                    <span key={c} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium border border-blue-100">
                                        {c}
                                    </span>
                                )) : <p className="text-gray-500 italic">No cuisine preferences</p>}
                            </div>
                        )}
                    </section>

                    {/* --- DISLIKES --- */}
                    <section>
                        <h2 className="text-lg font-bold text-gray-900 mb-4">Dislikes / Exclusions</h2>
                        {isEditing ? (
                            <input
                                type="text"
                                value={dislikes}
                                onChange={(e) => setDislikes(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#881C1B] focus:border-transparent transition-all"
                                placeholder="e.g., Mushrooms, Olives, Spicy Food"
                            />
                        ) : (
                            <p className="text-gray-800">{dislikes || <span className="text-gray-500 italic">None</span>}</p>
                        )}
                    </section>

                    {/* --- ACTION BUTTONS (Edit Mode Only) --- */}
                    {isEditing && (
                        <div className="flex gap-4 pt-4 border-t border-gray-100 mt-8">
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="flex-1 px-6 py-3 bg-[#881C1B] text-white font-medium rounded-lg hover:bg-[#6d1615] transition-colors disabled:opacity-50"
                            >
                                {isSaving ? 'Saving...' : 'Save Changes'}
                            </button>
                            <button
                                onClick={() => {
                                    setIsEditing(false);
                                    window.location.reload(); 
                                }}
                                disabled={isSaving}
                                className="px-6 py-3 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                            >
                                Cancel
                            </button>
                        </div>
                    )}
                </div>

                <div>
                    <button onClick={() => router.push('/chat')} className="mt-4 inline-block px-5 py-2 bg-[#881C1B] text-white rounded-md hover:bg-[#6d1615]">
                        Back to Chat
                    </button>
                </div>
            </div>
        </main>
    );
}