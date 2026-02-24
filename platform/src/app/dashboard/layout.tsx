'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import { BrainCircuit, Server, Route, PlayCircle, LogOut, Loader2, Camera } from 'lucide-react'

const navigation = [
    { name: 'Agents', href: '/dashboard', icon: Server },
    { name: 'Studio', href: '/dashboard/studio', icon: Camera },
    { name: 'Blueprints', href: '/dashboard/blueprints', icon: Route },
    { name: 'Execution', href: '/dashboard/execution', icon: PlayCircle },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname()
    const router = useRouter()
    const supabase = createClient()
    const [loading, setLoading] = useState(true)
    const [user, setUser] = useState<any>(null)

    useEffect(() => {
        const checkAuth = async () => {
            const { data: { session } } = await supabase.auth.getSession()
            if (!session) {
                router.push('/')
            } else {
                setUser(session.user)
                setLoading(false)
            }
        }
        checkAuth()
    }, [])

    const handleSignOut = async () => {
        await supabase.auth.signOut()
        router.push('/')
    }

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background flex">
            {/* Sidebar */}
            <div className="w-64 border-r border-border bg-zinc-950 flex flex-col">
                <div className="h-16 flex items-center px-6 border-b border-border">
                    <BrainCircuit className="w-6 h-6 text-primary mr-3" />
                    <span className="font-bold tracking-tight text-lg">IsoMind</span>
                </div>

                <nav className="flex-1 px-4 py-6 space-y-2 relative">
                    {/* Ambient background glow for sidebar */}
                    <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-[64px] pointer-events-none" />

                    {navigation.map((item) => {
                        const isActive = pathname === item.href
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={`flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 group ${isActive
                                    ? 'bg-primary/10 text-primary font-medium'
                                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50'
                                    }`}
                            >
                                <item.icon className={`w-5 h-5 mr-3 transition-colors ${isActive ? 'text-primary' : 'text-zinc-500 group-hover:text-zinc-300'}`} />
                                {item.name}
                            </Link>
                        )
                    })}
                </nav>

                <div className="p-4 border-t border-border">
                    <div className="mb-4 px-3">
                        <p className="text-xs text-zinc-500 uppercase font-semibold">Operator</p>
                        <p className="text-sm truncate text-zinc-300 mt-1">{user?.email}</p>
                    </div>
                    <button
                        onClick={handleSignOut}
                        className="w-full flex items-center px-3 py-2 text-sm text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                    >
                        <LogOut className="w-4 h-4 mr-2" />
                        Disconnect
                    </button>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 overflow-auto relative">
                {/* Subtle background glow for main area */}
                <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[128px] pointer-events-none" />
                <div className="absolute bottom-0 right-0 w-[300px] h-[300px] bg-emerald-500/5 rounded-full blur-[128px] pointer-events-none" />

                <main className="p-8 max-w-7xl mx-auto z-10 relative">
                    {children}
                </main>
            </div>
        </div>
    )
}
