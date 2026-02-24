'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase'
import { motion } from 'framer-motion'
import { Route, Play, Database, Clock, ChevronRight } from 'lucide-react'

export default function BlueprintsPage() {
    const [blueprints, setBlueprints] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const supabase = createClient()

    useEffect(() => {
        async function fetchBlueprints() {
            const { data, error } = await supabase
                .from('blueprints')
                .select('*')
                .order('created_at', { ascending: false })

            if (!error && data) {
                setBlueprints(data)
            }
            setLoading(false)
        }

        fetchBlueprints()
    }, [])

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Blueprints</h1>
                    <p className="text-zinc-400 mt-2 max-w-2xl">
                        A Blueprint is a recorded workflow (a Directed Acyclic Graph).
                        It stores the sequence of actions and the <b>Visual Anchors</b> you taught the agent in the Studio.
                    </p>
                </div>

                <button className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center border border-zinc-700">
                    <Database className="w-4 h-4 mr-2" />
                    Sync Memory
                </button>
            </div>

            {loading ? (
                <div className="flex justify-center py-20">
                    <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                </div>
            ) : blueprints.length === 0 ? (
                <div className="glass rounded-xl p-12 text-center flex flex-col items-center">
                    <div className="w-16 h-16 bg-zinc-900 rounded-full flex items-center justify-center mb-4">
                        <Route className="w-8 h-8 text-zinc-500" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">No Blueprints Found</h3>
                    <p className="text-zinc-400 max-w-md">
                        You haven't created any workflows yet. Head over to the <b>Studio</b> tab to capture a screen and record your first visual action.
                    </p>
                </div>
            ) : (
                <div className="space-y-4 mt-8">
                    {blueprints.map((bp, i) => {
                        const steps = bp.state_graph_json?.steps || []
                        const createdAt = new Date(bp.created_at).toLocaleDateString()

                        return (
                            <motion.div
                                key={bp.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className="glass rounded-xl p-6 border border-zinc-800 hover:border-primary/30 transition-all group"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center flex-1">
                                        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mr-4 border border-primary/20">
                                            <Route className="w-6 h-6 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-semibold flex items-center">
                                                {bp.name}
                                                <span className="bg-zinc-800 text-zinc-300 text-xs px-2 py-0.5 rounded ml-3 border border-zinc-700 font-mono">
                                                    {steps.length} steps
                                                </span>
                                            </h3>
                                            <div className="text-sm text-zinc-500 font-mono mt-1 flex items-center">
                                                {bp.id}
                                                <span className="mx-2">•</span>
                                                <Clock className="w-3 h-3 mr-1" />
                                                {createdAt}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex gap-3">
                                        <button className="text-primary hover:text-white bg-primary/10 hover:bg-primary px-4 py-2 rounded-lg font-medium transition-colors flex items-center border border-primary/20 hover:border-primary">
                                            <Play className="w-4 h-4 mr-2" />
                                            Execute
                                        </button>
                                    </div>
                                </div>

                                {/* Workflow Preview */}
                                <div className="mt-6 pt-4 border-t border-zinc-800/50 flex flex-wrap gap-2">
                                    {steps.slice(0, 5).map((step: any, j: number) => (
                                        <div key={j} className="flex items-center">
                                            {j > 0 && <ChevronRight className="w-4 h-4 text-zinc-600 mx-2" />}
                                            <span className={`text-xs px-2.5 py-1.5 rounded-lg border flex items-center font-medium ${step.action === 'click' ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                                                }`}>
                                                {step.action.toUpperCase()}: {step.semantic_target || step.text || '?'}
                                            </span>
                                        </div>
                                    ))}
                                    {steps.length > 5 && (
                                        <div className="flex items-center">
                                            <ChevronRight className="w-4 h-4 text-zinc-600 mx-2" />
                                            <span className="text-xs px-2.5 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-400 font-medium">
                                                +{steps.length - 5} more
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
