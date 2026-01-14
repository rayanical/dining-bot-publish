/**
 * Onboarding Wizard.
 *
 * A multi-step form to collect user dietary preferences and goals after initial signup.
 * Steps:
 * 1. Welcome
 * 2. Dietary Constraints (Vegan, Allergies)
 * 3. Health Goals (Muscle gain, weight loss)
 * 4. Liked Cuisines
 * 5. Dislikes/Exclusions
 *
 * Submits the profile to the backend upon completion.
 *
 * @module app/onboarding/page
 */

'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

const Checkbox = ({ label, isChecked, onChange }: { label: string; isChecked: boolean; onChange: () => void }) => (
    <label className="flex items-center space-x-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all cursor-pointer">
        <input type="checkbox" checked={isChecked} onChange={onChange} className="h-5 w-5 rounded border-gray-300 text-[#881C1B] focus:ring-[#881C1B]" />
        <span className="text-gray-800">{label}</span>
    </label>
);

const SelectableCard = ({ title, isSelected, onClick }: { title: string; isSelected: boolean; onClick: () => void }) => (
    <button
        type="button"
        onClick={onClick}
        className={`flex-1 min-w-[200px] p-6 rounded-lg border-2 text-center transition-all ${
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
        className={`px-4 py-2 rounded-full border transition-all ${
            isSelected ? 'bg-[#881C1B] text-white border-[#881C1B]' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'
        }`}
    >
        {label}
    </button>
);

export default function OnboardingPage() {
    /**
     * Collects dietary preferences, allergies, goals, liked cuisines, and dislikes across steps.
     */
    const [step, setStep] = useState(1);
    const [diets, setDiets] = useState<string[]>([]);
    const [allergies, setAllergies] = useState('');
    const [goal, setGoal] = useState('');
    const [cuisines, setCuisines] = useState<string[]>([]);
    const [dislikes, setDislikes] = useState('');

    const router = useRouter();
    const supabase = createClient();
    const totalSteps = 5;

    useEffect(() => {
        const checkUserSession = async () => {
            const { data, error } = await supabase.auth.getUser();
            if (error || !data.user) {
                router.push('/');
            }
        };
        checkUserSession();
    }, [supabase, router]);

    const toggleItem = (list: string[], setter: (list: string[]) => void, item: string) => {
        if (list.includes(item)) {
            setter(list.filter((i) => i !== item));
        } else {
            setter([...list, item]);
        }
    };

    const nextStep = () => setStep((prev) => (prev < totalSteps ? prev + 1 : prev));
    const prevStep = () => setStep((prev) => (prev > 1 ? prev - 1 : prev));

    const handleSubmit = async () => {
        try {
            const {
                data: { user },
            } = await supabase.auth.getUser();
            if (!user) {
                alert('Please log in first');
                return;
            }

            const allergyList = allergies
                .split(',')
                .map((s) => s.trim())
                .filter((s) => s.length > 0);

            const payload = {
                user_id: user.id,
                email: user.email || '',
                diets: diets,
                allergies: allergyList,
                goal: goal,
                dislikes: dislikes,
                liked_cuisines: cuisines
            };

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/profile`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error('Failed to save profile');
            }

            router.push('/chat');
        } catch {
            alert('Failed to save profile. Is the backend running?');
        }
    };

    const dietOptions = ['Vegan', 'Vegetarian', 'Halal', 'Kosher'];
    const goalOptions = ['Lose Weight', 'Maintain Weight', 'Gain Muscle / Weight', 'Just Exploring'];
    const cuisineOptions = ['Mediterranean', 'East Asian', 'Tandoori / South Asian', 'Mexican / Latin American', 'Italian (Pizza, Pasta)', 'American Comfort', 'Salads & Sandwiches'];

    const Step1_Welcome = (
        <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900">Welcome to the UMass Dining Bot</h1>
            <p className="mt-4 text-lg text-gray-600">
                Let&#39;s create your personal nutrition profile. This will help me give you meal plans and recommendations tailored just for you.
            </p>
        </div>
    );

    const Step2_Constraints = (
        <div>
            <h2 className="text-2xl font-semibold text-gray-900">First, what should we avoid?</h2>
            <p className="mt-2 text-gray-600">Select any dietary restrictions.</p>
            <div className="mt-6 space-y-4">
                <h3 className="font-medium text-gray-800">Diets</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {dietOptions.map((item) => (
                        <Checkbox key={item} label={item} isChecked={diets.includes(item)} onChange={() => toggleItem(diets, setDiets, item)} />
                    ))}
                </div>
                <h3 className="font-medium text-gray-800 pt-4">Allergies & Intolerances</h3>
                <input
                    type="text"
                    value={allergies}
                    onChange={(e) => setAllergies(e.target.value)}
                    className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#881C1B] focus:border-[#881C1B] text-gray-900"
                    placeholder="e.g., Peanuts, Dairy, Gluten, Shellfish"
                />
            </div>
        </div>
    );

    const Step3_Goals = (
        <div>
            <h2 className="text-2xl font-semibold text-gray-900">What are your primary health goals?</h2>
            <p className="mt-2 text-gray-600">Knowing your goals helps me create meal plans that fit your needs.</p>
            <div className="mt-6 flex flex-wrap gap-4 justify-center">
                {goalOptions.map((item) => (
                    <SelectableCard key={item} title={item} isSelected={goal === item} onClick={() => setGoal(item)} />
                ))}
            </div>
        </div>
    );

    const Step4_Likes = (
        <div>
            <h2 className="text-2xl font-semibold text-gray-900">What do you *like* to eat?</h2>
            <p className="mt-2 text-gray-600">Select any cuisines you enjoy.</p>
            <div className="mt-6 flex flex-wrap gap-3">
                {cuisineOptions.map((item) => (
                    <SelectableTag key={item} label={item} isSelected={cuisines.includes(item)} onClick={() => toggleItem(cuisines, setCuisines, item)} />
                ))}
            </div>
        </div>
    );

    const Step5_Dislikes = (
        <div>
            <h2 className="text-2xl font-semibold text-gray-900">Almost done! Anything you just plain dislike?</h2>
            <p className="mt-2 text-gray-600">This helps me avoid suggesting foods you know you won&#39;t eat.</p>
            <div className="mt-6">
                <input
                    type="text"
                    value={dislikes}
                    onChange={(e) => setDislikes(e.target.value)}
                    className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#881C1B] focus:border-[#881C1B] text-gray-900"
                    placeholder="e.g., Olives, Spicy Food, Tofu, Mushrooms"
                />
            </div>
        </div>
    );

    return (
        <main className="flex flex-col items-center justify-center h-screen bg-gray-100 p-4">
            <div className="w-full max-w-2xl bg-white rounded-lg shadow-xl overflow-hidden">
                <div className="w-full bg-gray-200">
                    <div className="h-2 bg-[#881C1B] transition-all duration-300" style={{ width: `${(step / totalSteps) * 100}%` }}></div>
                </div>

                <div className="p-8 md:p-12 min-h-[400px] flex flex-col justify-center">
                    {step === 1 && Step1_Welcome}
                    {step === 2 && Step2_Constraints}
                    {step === 3 && Step3_Goals}
                    {step === 4 && Step4_Likes}
                    {step === 5 && Step5_Dislikes}
                </div>

                <div className="flex justify-between items-center p-4 bg-gray-50 border-t">
                    <button
                        onClick={prevStep}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                            step === 1 ? 'text-gray-400 cursor-not-allowed' : 'text-gray-700 bg-gray-200 hover:bg-gray-300'
                        }`}
                        disabled={step === 1}
                    >
                        Back
                    </button>
                    {step < totalSteps ? (
                        <button onClick={nextStep} className="px-6 py-2 rounded-md text-sm font-medium text-white bg-[#881C1B] hover:bg-[#6d1615]">
                            Next
                        </button>
                    ) : (
                        <button onClick={handleSubmit} className="px-6 py-2 rounded-md text-sm font-medium text-white bg-green-600 hover:bg-green-700">
                            Finish & Start Chatting
                        </button>
                    )}
                </div>
            </div>
        </main>
    );
}