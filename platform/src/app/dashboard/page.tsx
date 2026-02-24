'use client'

import { motion } from 'framer-motion'
import { Server, Activity, Plus, Settings } from 'lucide-react'

// Mock Data for now
const agents = [
    { id: 'ag-1', name: 'Alpha Runner', status: 'Online', gpu: 'RTX 3090', ip: '217.171.200.22', uptime: '14h 23m' },
    { id: 'ag-2', name: 'Beta Observer', status: 'Offline', gpu: 'RTX 4090', ip: 'Unknown', uptime: '-' },
]

export default function AgentsPage() {
    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">IsoMind Command Center</h1>
                    <p className="text-zinc-400 mt-2 max-w-2xl">
                        Welcome to the visual AI orchestration platform. IsoMind uses <b>Visual RAG</b> to teach agents
                        what UI elements look like, allowing them to autonomously navigate the web without brittle HTML scraping.
                    </p>
                </div>

                <button className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center shadow-[0_0_15px_rgba(59,130,246,0.5)]">
                    <Plus className="w-4 h-4 mr-2" />
                    Provision Agent
                </button>
            </div>

            {/* Explainer Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-colors pointer-events-none" />
                    <div className="w-10 h-10 bg-primary/20 text-primary rounded-lg flex items-center justify-center mb-4">
                        <span className="font-bold text-lg">1</span>
                    </div>
                    <h3 className="text-lg font-bold mb-2">Teach in Studio</h3>
                    <p className="text-sm text-zinc-400">
                        Go to the <b>Studio</b> tab. Capture a screenshot from a live agent and click on elements. The system will crop the UI element, embed it via CLIP, and save it as a "Visual Memory".
                    </p>
                </div>

                <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-colors pointer-events-none" />
                    <div className="w-10 h-10 bg-emerald-500/20 text-emerald-500 rounded-lg flex items-center justify-center mb-4">
                        <span className="font-bold text-lg">2</span>
                    </div>
                    <h3 className="text-lg font-bold mb-2">Build Blueprints</h3>
                    <p className="text-sm text-zinc-400">
                        Review the <b>Blueprints</b> tab. Your taught actions automatically form a step-by-step DAG (Directed Acyclic Graph) defining the exact visual workflow for the agent.
                    </p>
                </div>

                <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/10 rounded-full blur-2xl group-hover:bg-purple-500/20 transition-colors pointer-events-none" />
                    <div className="w-10 h-10 bg-purple-500/20 text-purple-400 rounded-lg flex items-center justify-center mb-4">
                        <span className="font-bold text-lg">3</span>
                    </div>
                    <h3 className="text-lg font-bold mb-2">Live Execution</h3>
                    <p className="text-sm text-zinc-400">
                        Trigger the workflow in the <b>Execution</b> tab. The agent uses Qwen2-VL and cosine similarity to find the visual anchors on its live screen and autonomously clicks them.
                    </p>
                </div>
            </div>

            <div>
                <h2 className="text-xl font-bold mt-4 mb-4">Active Fleet Nodes</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {agents.map((agent, i) => (
                        <motion.div
                            key={agent.id}
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: i * 0.1 }}
                            className="glass rounded-xl p-6 border border-zinc-800 hover:border-zinc-700 transition-colors"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex flex-col">
                                    <span className="text-lg font-semibold">{agent.name}</span>
                                    <span className="text-xs text-zinc-500 font-mono mt-1">{agent.id}</span>
                                </div>

                                <div className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center ${agent.status === 'Online' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
                                    }`}>
                                    {agent.status === 'Online' && <Activity className="w-3 h-3 mr-1.5 animate-pulse" />}
                                    {agent.status}
                                </div>
                            </div>

                            <div className="space-y-3 mb-6 bg-zinc-900/50 p-4 rounded-lg">
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Node IP:</span>
                                    <span className="text-zinc-300 font-mono">{agent.ip}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Hardware:</span>
                                    <span className="text-primary">{agent.gpu}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-zinc-500">Uptime:</span>
                                    <span className="text-zinc-300">{agent.uptime}</span>
                                </div>
                            </div>

                            <div className="flex gap-2">
                                <button disabled={agent.status !== 'Online'} className="flex-1 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-lg transition-colors flex justify-center items-center">
                                    <Server className="w-4 h-4 mr-2" />
                                    Connect
                                </button>
                                <button className="p-2 border border-zinc-700 hover:bg-zinc-800 rounded-lg text-zinc-400 transition-colors">
                                    <Settings className="w-4 h-4" />
                                </button>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    )
}
