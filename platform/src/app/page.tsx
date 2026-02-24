'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase'
import { motion, AnimatePresence } from 'framer-motion'
import { BrainCircuit, Loader2, ArrowRight, Mail } from 'lucide-react'
import { useRouter } from 'next/navigation'

type AuthMode = 'login' | 'signup' | 'forgot_password'

export default function LoginPage() {
  const [mode, setMode] = useState<AuthMode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const router = useRouter()
  const supabase = createClient()

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setMessage(null)

    try {
      if (mode === 'signup') {
        const { error } = await supabase.auth.signUp({
          email,
          password,
        })
        if (error) throw error
        setMessage('Check your email for the confirmation link.')
      } else if (mode === 'login') {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })
        if (error) throw error
        router.push('/dashboard')
      } else if (mode === 'forgot_password') {
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: `${window.location.origin}/dashboard/reset-password`,
        })
        if (error) throw error
        setMessage('Password reset instructions sent to your email.')
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4 relative overflow-hidden bg-background">
      {/* Background decoration */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[128px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-[128px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md z-10"
      >
        <div className="glass rounded-2xl p-8 shadow-2xl border border-white/10">
          <div className="flex flex-col items-center mb-8">
            <div className="h-16 w-16 bg-primary/10 rounded-2xl flex items-center justify-center mb-4 border border-primary/20 shadow-[0_0_30px_rgba(59,130,246,0.2)]">
              <BrainCircuit className="w-8 h-8 text-primary" />
            </div>
            <h1 className="text-3xl font-bold text-center tracking-tight">IsoMind Platform</h1>
            <p className="text-muted-foreground text-center mt-2">
              {mode === 'login' && 'Sign in to orchestrate your agents.'}
              {mode === 'signup' && 'Create an account to get started.'}
              {mode === 'forgot_password' && 'Reset your password.'}
            </p>
          </div>

          {/* Mode Switcher */}
          {mode !== 'forgot_password' && (
            <div className="flex bg-zinc-900/50 p-1 rounded-lg mb-6 border border-zinc-800">
              <button
                type="button"
                onClick={() => { setMode('login'); setError(null); setMessage(null); }}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${mode === 'login' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'}`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => { setMode('signup'); setError(null); setMessage(null); }}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${mode === 'signup' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'}`}
              >
                Create Account
              </button>
            </div>
          )}

          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 text-zinc-300">Email Address</label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg pl-10 pr-4 py-3 outline-none focus:ring-2 focus:ring-primary/50 transition-all text-white placeholder-zinc-500"
                  placeholder="operator@isomind.ai"
                />
                <Mail className="w-4 h-4 text-zinc-500 absolute left-3.5 top-3.5" />
              </div>
            </div>

            <AnimatePresence mode="popLayout">
              {mode !== 'forgot_password' && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <label className="block text-sm font-medium mb-1 text-zinc-300">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-primary/50 transition-all text-white placeholder-zinc-500"
                    placeholder="••••••••"
                  />
                  {mode === 'login' && (
                    <div className="flex justify-end mt-2">
                      <button
                        type="button"
                        onClick={() => { setMode('forgot_password'); setError(null); setMessage(null); }}
                        className="text-xs text-primary hover:underline"
                      >
                        Forgot password?
                      </button>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-3 rounded-lg text-sm text-center">
                {error}
              </div>
            )}

            {message && (
              <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-3 rounded-lg text-sm text-center">
                {message}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary hover:bg-blue-600 text-white rounded-lg px-4 py-3 font-medium transition-all flex items-center justify-center group disabled:opacity-70 disabled:cursor-not-allowed mt-6 shadow-[0_0_15px_rgba(59,130,246,0.3)]"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  {mode === 'login' ? 'Sign In' : mode === 'signup' ? 'Create Account' : 'Send Reset Link'}
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>

            {mode === 'forgot_password' && (
              <button
                type="button"
                onClick={() => setMode('login')}
                className="w-full text-zinc-400 hover:text-white text-sm mt-4 transition-colors"
              >
                Back to login
              </button>
            )}
          </form>
        </div>
      </motion.div>
    </div>
  )
}
