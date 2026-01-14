/**
 * Landing Page.
 *
 * The public marketing page for the Dining Bot application.
 * It explains features, benefits, and provides entry points to Login/Signup.
 *
 * @module app/page
 */

'use client';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { UtensilsCrossed, Target, TrendingUp, Calendar, MessageSquare, Sparkles, ChevronRight, CheckCircle2, Leaf, Apple, Heart } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function LandingPage() {
    const router = useRouter();
    const redirectToLogin = () => {
        router.push('/login');
    };

    const scrollToSection = (sectionId: string) => {
        const element = document.getElementById(sectionId);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    };

    const sendToDemo = () => {
        window.open('https://drive.google.com/file/d/1J_EoXbgtIPgcSRqCjgOEO-JcZhV8FLIx/view?usp=drive_link')
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-white via-red-50 to-white">
            <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex items-center space-x-2">
                            <div className="w-10 h-10 bg-gradient-to-br from-[#881c1c] to-[#a52a2a] rounded-lg flex items-center justify-center">
                                <UtensilsCrossed className="w-6 h-6 text-white" />
                            </div>
                            <span className="text-xl font-bold text-[#881c1c]">UMass Dining Bot</span>
                        </div>
                        <div className="flex items-center space-x-4">
                            <Button variant="ghost" className="text-gray-700 hover:text-[#881c1c]" onClick={()=>scrollToSection('features')}>
                                Features
                            </Button>
                            <Button variant="ghost" className="text-gray-700 hover:text-[#881c1c]" onClick={()=>scrollToSection('about')}>
                                About
                            </Button>
                            <Button className="bg-[#881c1c] hover:bg-[#6d1616] text-white" onClick={redirectToLogin}>
                                Get Started
                            </Button>
                        </div>
                    </div>
                </div>
            </nav>

            <section id="about" className="relative overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
                    <div className="grid lg:grid-cols-2 gap-12 items-center">
                        <div className="space-y-8">
                            <Badge className="bg-[#881c1c]/10 text-[#881c1c] hover:bg-[#881c1c]/20 border-[#881c1c]/20">
                                <Sparkles className="w-3 h-3 mr-1" />
                                AI-Powered Nutrition Assistant
                            </Badge>
                            <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
                                Your Personal <span className="text-[#881c1c] bg-clip-text">Dining Companion</span> at UMass
                            </h1>
                            <p className="text-xl text-gray-600 leading-relaxed">
                                Navigate dining halls with ease. Upload dietary constraints, set health goals, and get personalized meal plans tailored to your unique needs. Making
                                healthy eating effortless for the entire UMass community.
                            </p>
                            <div className="flex flex-col sm:flex-row gap-4">
                                <Button
                                    size="lg"
                                    className="bg-[#881c1c] hover:bg-[#6d1616] text-white text-lg px-8 py-6 shadow-lg hover:shadow-xl transition-all"
                                    onClick={redirectToLogin}
                                >
                                    Start Your Journey
                                    <ChevronRight className="ml-2 w-5 h-5" />
                                </Button>
                                <Button size="lg" variant="outline" className="border-[#881c1c] text-[#881c1c] hover:bg-[#881c1c]/5 text-lg px-8 py-6" onClick={sendToDemo}>
                                    Watch Demo
                                </Button>
                            </div>
                            <div className="flex items-center space-x-8 pt-4">
                                <div>
                                    <div className="text-3xl font-bold text-[#881c1c]">4</div>
                                    <div className="text-sm text-gray-600">Dining Halls</div>
                                </div>
                                <div className="h-12 w-px bg-gray-300"></div>
                                <div>
                                    <div className="text-3xl font-bold text-[#881c1c]">2,000+</div>
                                    <div className="text-sm text-gray-600">Meals Indexed</div>
                                </div>
                            </div>
                        </div>
                        <div className="relative">
                            <div className="max-w-md mx-auto rounded-2xl overflow-hidden border border-black/10 shadow-lg">
                                <div className="bg-[#881c1c] text-white p-5">
                                    <div className="flex items-center space-x-3">
                                        <MessageSquare className="w-6 h-6" />
                                        <h3 className="text-2xl font-bold">Chat with Dining Bot</h3>
                                    </div>
                                    <p className="text-red-100 ml-9">Get instant meal recommendations</p>
                                </div>

                                <div className="bg-white p-5 space-y-4">
                                    <div className="bg-gray-100 rounded-xl p-4">
                                        <p className="text-sm font-medium text-gray-600">You</p>
                                        <p className="font-medium text-gray-900">I need high protein vegan options for today</p>
                                    </div>

                                    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                                        <p className="text-sm font-bold text-[#881c1c]">Dining Bot</p>
                                        <p className="text-gray-800 mt-1">
                                            Perfect! Based on your profile, I recommend the Tofu Scramble at Worcester (28g protein) and Black Bean Burger at Franklin (24g protein).
                                            Both align with your 2,200 calorie goal.
                                        </p>

                                        <div className="flex gap-2 mt-3">
                                            <span className="flex items-center text-xs font-medium bg-white border border-gray-200 rounded-full px-3 py-1">
                                                <Apple className="w-3 h-3 mr-1.5" />
                                                28g protein
                                            </span>
                                            <span className="flex items-center text-xs font-medium bg-white border border-gray-200 rounded-full px-3 py-1">
                                                <Leaf className="w-3 h-3 mr-1.5" />
                                                Vegan
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section id="features" className="py-20 bg-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center space-y-4 mb-16">
                        <h2 className="text-4xl lg:text-5xl font-bold text-gray-900">
                            Powerful Features for <span className="text-[#881c1c]">Your Health</span>
                        </h2>
                        <p className="text-xl text-gray-600 max-w-3xl mx-auto">Everything you need to make informed dining decisions and achieve your nutrition goals</p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        <Card className="border-2 hover:border-[#881c1c]/30 transition-all duration-300 hover:shadow-lg">
                            <CardHeader>
                                <div className="w-12 h-12 bg-[#881c1c]/10 rounded-lg flex items-center justify-center mb-4">
                                    <UtensilsCrossed className="w-6 h-6 text-[#881c1c]" />
                                </div>
                                <CardTitle className="text-xl">Dietary Constraints</CardTitle>
                                <CardDescription>Upload restrictions like vegan, gluten-free, or specific allergies. Get meals that perfectly match your needs.</CardDescription>
                            </CardHeader>
                        </Card>

                        <Card className="border-2 hover:border-[#881c1c]/30 transition-all duration-300 hover:shadow-lg">
                            <CardHeader>
                                <div className="w-12 h-12 bg-[#881c1c]/10 rounded-lg flex items-center justify-center mb-4">
                                    <Target className="w-6 h-6 text-[#881c1c]" />
                                </div>
                                <CardTitle className="text-xl">Health Goals</CardTitle>
                                <CardDescription>Set weight loss, muscle gain, or maintenance goals. Track progress with personalized nutrition targets.</CardDescription>
                            </CardHeader>
                        </Card>

                        <Card className="border-2 hover:border-[#881c1c]/30 transition-all duration-300 hover:shadow-lg">
                            <CardHeader>
                                <div className="w-12 h-12 bg-[#881c1c]/10 rounded-lg flex items-center justify-center mb-4">
                                    <Calendar className="w-6 h-6 text-[#881c1c]" />
                                </div>
                                <CardTitle className="text-xl">Daily Meal Plans</CardTitle>
                                <CardDescription>Generate complete meal plans with calories and nutritional facts for breakfast, lunch, and dinner.</CardDescription>
                            </CardHeader>
                        </Card>

                        <Card className="border-2 hover:border-[#881c1c]/30 transition-all duration-300 hover:shadow-lg">
                            <CardHeader>
                                <div className="w-12 h-12 bg-[#881c1c]/10 rounded-lg flex items-center justify-center mb-4">
                                    <TrendingUp className="w-6 h-6 text-[#881c1c]" />
                                </div>
                                <CardTitle className="text-xl">Smart Tracking</CardTitle>
                                <CardDescription>Log foods and track past meals. The bot learns your preferences and creates an evolving nutrition profile.</CardDescription>
                            </CardHeader>
                        </Card>

                        <Card className="border-2 hover:border-[#881c1c]/30 transition-all duration-300 hover:shadow-lg">
                            <CardHeader>
                                <div className="w-12 h-12 bg-[#881c1c]/10 rounded-lg flex items-center justify-center mb-4">
                                    <MessageSquare className="w-6 h-6 text-[#881c1c]" />
                                </div>
                                <CardTitle className="text-xl">Natural Conversation</CardTitle>
                                <CardDescription>Ask questions like &quot;Where&#39;s the best vegan protein today?&quot; Get instant, accurate answers through chat.</CardDescription>
                            </CardHeader>
                        </Card>

                        <Card className="border-2 hover:border-[#881c1c]/30 transition-all duration-300 hover:shadow-lg">
                            <CardHeader>
                                <div className="w-12 h-12 bg-[#881c1c]/10 rounded-lg flex items-center justify-center mb-4">
                                    <Heart className="w-6 h-6 text-[#881c1c]" />
                                </div>
                                <CardTitle className="text-xl">Gap Detection</CardTitle>
                                <CardDescription>Identifies nutritional gaps in your diet and suggests meals to fill them for optimal health.</CardDescription>
                            </CardHeader>
                        </Card>
                    </div>
                </div>
            </section>

            <section className="py-20 bg-gradient-to-br from-[#881c1c] to-[#a52a2a] text-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-center">
                        <div className="space-y-6 text-center">
                            <h2 className="text-4xl lg:text-5xl font-bold">Why UMass Students Love Our Bot</h2>
                            <p className="text-xl text-red-100">Join other students in making healthier choices every day!</p>
                            <div className="space-y-4 inline-block text-left">
                                {[
                                    'Save time navigating multiple dining hall menus',
                                    'Meet dietary restrictions without compromise',
                                    'Achieve fitness goals with personalized nutrition',
                                    'Discover new meals based on your taste preferences',
                                    'Track progress and adapt recommendations over time',
                                ].map((benefit, index) => (
                                    <div key={index} className="flex items-start space-x-3">
                                        <CheckCircle2 className="w-6 h-6 flex-shrink-0 mt-1" />
                                        <span className="text-lg">{benefit}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="py-20 bg-white">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8">
                    <h2 className="text-4xl lg:text-5xl font-bold text-gray-900">
                        Ready to Transform Your <span className="text-[#881c1c]">Dining Experience?</span>
                    </h2>
                    <p className="text-xl text-gray-600">Start making smarter, healthier food choices today with personalized guidance from our AI-powered dining assistant.</p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                        <Button size="lg" className="bg-[#881c1c] hover:bg-[#6d1616] text-white text-lg px-8 py-6 shadow-lg hover:shadow-xl transition-all" onClick={redirectToLogin}>
                            Join Today
                            <ChevronRight className="ml-2 w-5 h-5" />
                        </Button>
                        <Button size="lg" variant="outline" className="border-[#881c1c] text-[#881c1c] hover:bg-[#881c1c]/5 text-lg px-8 py-6">
                            Learn More
                        </Button>
                    </div>
                </div>
            </section>

            <footer className="border-t bg-gray-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                    <div className="">
                        <div className="space-y-4 flex flex-col items-center text-center">
                            <div className="flex items-center space-x-2">
                                <div className="w-8 h-8 bg-gradient-to-br from-[#881c1c] to-[#a52a2a] rounded-lg flex items-center justify-center">
                                    <UtensilsCrossed className="w-5 h-5 text-white" />
                                </div>
                                <span className="font-bold text-[#881c1c]">UMass Dining Bot</span>
                            </div>
                            <p className="text-sm text-gray-600">Your personal AI nutrition assistant for the UMass Amherst dining experience.</p>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}