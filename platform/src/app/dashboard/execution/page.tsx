'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { createClient } from '@/lib/supabase'
import { Play, Square, Loader2, MonitorPlay, Terminal, AlertCircle } from 'lucide-react'

export default function ExecutionPage() {
    const [blueprints, setBlueprints] = useState<any[]>([])
    const [selectedBlueprint, setSelectedBlueprint] = useState('')
    const [status, setStatus] = useState<'IDLE' | 'STARTING' | 'RUNNING' | 'COMPLETED' | 'ERROR'>('IDLE')

    // Inject Vercel build info into the initial logs so the user knows the exact version
    const [logs, setLogs] = useState<string[]>([
        `[SYSTEM] Dashboard UI Version: ${process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA?.substring(0, 7) || 'Local'}`,
        `[SYSTEM] Environment: ${process.env.NEXT_PUBLIC_VERCEL_ENV || 'development'}`
    ])

    const supabase = createClient()

    // Mock Agent Data
    const agentIp = "217.171.200.22"

    useEffect(() => {
        async function fetchBlueprints() {
            const { data } = await supabase.from('blueprints').select('id, name').order('created_at', { ascending: false })
            if (data) setBlueprints(data)

            if (typeof window !== 'undefined') {
                const params = new URLSearchParams(window.location.search)
                const bpId = params.get('blueprintId')
                if (bpId) setSelectedBlueprint(bpId)
            }
        }
        fetchBlueprints()
    }, [])

    const handleExecute = async () => {
        if (!selectedBlueprint) return

        setStatus('STARTING')
        setLogs([`[SYSTEM] Connecting to Local Orchestration API...`])

        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';
            const response = await fetch(`${API_URL}/v1/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    blueprint_id: selectedBlueprint,
                    start_url: 'https://example.com' // Hardcoded for demo
                })
            });

            if (!response.body) throw new Error('No response body');

            setStatus('RUNNING')

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.replace('data: ', '');
                        if (data.trim()) {
                            setLogs(prev => [...prev, data]);
                        }
                        if (data.includes('✅') || data.includes('Fatal exception') || data.includes('Execution halted')) {
                            setStatus(data.includes('❌') || data.includes('Fatal') ? 'ERROR' : 'COMPLETED');
                        }
                    }
                }
            }
        } catch (e: any) {
            setStatus('ERROR')
            setLogs(prev => [...prev, `[ERROR] Failed to connect to API: ${e.message}`])
        }
    }

    const handleStop = () => {
        setStatus('IDLE')
        setLogs(prev => [...prev, `[SYSTEM] Execution aborted by operator.`])
    }

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)]">
            <div className="flex items-end justify-between mb-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Live Execution</h1>
                    <p className="text-zinc-400 mt-2 max-w-2xl">
                        Select a Blueprint and press Start. The agent uses <b>Qwen2-VL</b> and Cosine Similarity to compare your recorded
                        Visual Anchors against the live screen, clicking the highest probability matches autonomously.
                    </p>
                </div>

                <div className="flex items-center gap-4 bg-zinc-900/50 p-2 rounded-xl border border-zinc-800">
                    <select
                        value={selectedBlueprint}
                        onChange={(e) => setSelectedBlueprint(e.target.value)}
                        disabled={status !== 'IDLE'}
                        className="bg-zinc-800 border-none text-sm text-white rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-primary w-64 appearance-none"
                    >
                        <option value="">Select a Blueprint...</option>
                        {blueprints.map(bp => (
                            <option key={bp.id} value={bp.id}>{bp.name}</option>
                        ))}
                    </select>

                    {status === 'IDLE' || status === 'COMPLETED' || status === 'ERROR' ? (
                        <button
                            onClick={handleExecute}
                            disabled={!selectedBlueprint}
                            className="bg-primary hover:bg-blue-600 disabled:opacity-50 disabled:bg-zinc-800 disabled:text-zinc-500 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center"
                        >
                            <Play className="w-4 h-4 mr-2" />
                            Start Task
                        </button>
                    ) : (
                        <button
                            onClick={handleStop}
                            className="bg-red-500 hover:bg-red-600 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center"
                        >
                            <Square className="w-4 h-4 mr-2" />
                            Abort Forcefully
                        </button>
                    )}
                </div>
            </div>

            <div className="flex gap-6 flex-1 min-h-0">
                {/* Left Side: VNC / WebRTC Stream */}
                <div className="flex-1 glass rounded-xl border border-zinc-800 overflow-hidden flex flex-col relative">
                    <div className="h-10 border-b border-zinc-800 bg-zinc-900/80 flex items-center px-4 justify-between">
                        <div className="flex items-center text-sm font-medium text-zinc-300">
                            <MonitorPlay className="w-4 h-4 text-emerald-400 mr-2" />
                            Agent Visual Output ({agentIp})
                        </div>
                        {status === 'RUNNING' && (
                            <div className="flex items-center text-xs text-primary animate-pulse">
                                <span className="w-2 h-2 rounded-full bg-primary mr-2" />
                                Processing Vision Frame
                            </div>
                        )}
                    </div>

                    <div className="flex-1 bg-black relative flex items-center justify-center">
                        {/* 
              This is where we embed the noVNC player. 
              For now we use a styling placeholder until the actual SSH API tunnels are bridged to Next.js.
            */}
                        {status === 'IDLE' ? (
                            <div className="text-zinc-600 flex flex-col items-center">
                                <Play className="w-16 h-16 mb-4 opacity-20" />
                                <p>Awaiting Execution Command</p>
                            </div>
                        ) : (
                            <div className="absolute inset-0 w-full h-full group">
                                <div className="absolute inset-0 z-10 hidden group-hover:flex items-center justify-center bg-black/50 pointer-events-none transition-opacity">
                                    {status === 'STARTING' && <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />}
                                    <span className="text-white/70 text-sm font-medium">Remote Stream Bridged via WebRTC/Proxy</span>
                                </div>
                                <iframe
                                    src="/api/proxy/vnc"
                                    className="w-full h-full outline-none border-none"
                                    title="Agent Live VNC Stream"
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Side: Terminal Logs */}
                <div className="w-96 glass rounded-xl border border-zinc-800 flex flex-col">
                    <div className="h-10 border-b border-zinc-800 bg-zinc-900/80 flex items-center px-4">
                        <Terminal className="w-4 h-4 text-zinc-400 mr-2" />
                        <span className="text-sm font-medium text-zinc-300">Orchestrator Logs</span>
                    </div>

                    <div className="flex-1 p-4 overflow-y-auto font-mono text-xs flex flex-col gap-2">
                        {logs.length === 0 ? (
                            <div className="text-zinc-600 mt-4 text-center">No logs generated yet.</div>
                        ) : (
                            logs.map((log, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className={`${log.includes('ERROR') || log.includes('aborted') || log.includes('❌') ? 'text-red-400' : log.includes('SYSTEM') ? 'text-primary' : 'text-emerald-400'}`}
                                >
                                    <span className="text-zinc-600 mr-2">{new Date().toLocaleTimeString().split(' ')[0]}</span>
                                    {log}
                                </motion.div>
                            ))
                        )}

                        {status === 'RUNNING' && (
                            <div className="flex items-center text-zinc-500 mt-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-pulse mr-2" />
                                Waiting for VLM Inference...
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
