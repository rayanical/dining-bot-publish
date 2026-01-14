# 🖥️ Dining Bot Frontend

The user interface for the Dining Bot, built with Next.js 16 and React 19. It uses the Vercel AI SDK for streaming chat responses and Supabase SSR for authentication.

## ⚡ Tech Stack

-   **Framework:** Next.js 16 (App Router)
-   **Language:** TypeScript
-   **Styling:** Tailwind CSS v4, Shadcn UI
-   **State/Data:** Supabase Auth & SSR
-   **AI Integration:** Vercel AI SDK (`@ai-sdk/react`)
-   **Icons:** Lucide React

## 🛠️ Setup & Installation

### 1. Install Dependencies

We use `bun` for package management, but npm works too.

```bash
cd frontend
bun install
```

### 2. Environment Variables

Create a `.env.local` file in the `frontend` directory:

```env
# Supabase Configuration (Found in your Supabase Project Settings > API)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend URL (Default is localhost for dev)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
bun dev
```

The app will be available at `http://localhost:3000`.

## 📂 Key Directories

-   `app/chat`: The main AI chat interface.
-   `app/dashboard`: User nutrition tracking and logs.
-   `app/meal-builder`: Algorithmic meal planning UI.
-   `app/onboarding`: Initial user profile setup wizard.
-   `lib/supabase`: Client-side Supabase utilities.

## 📝 Notes

-   Ensure the backend API is running on port 8000 before starting the frontend.
-   Authentication flows require properly configured Supabase redirect URLs.
