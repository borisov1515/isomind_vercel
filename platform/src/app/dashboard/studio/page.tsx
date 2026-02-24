'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { createClient } from '@/lib/supabase'
import { Camera, MousePointer2, Image as ImageIcon, CheckCircle, Plus, Loader2, Play } from 'lucide-react'

export default function StudioPage() {
    const [blueprints, setBlueprints] = useState<any[]>([])
    const [selectedBlueprint, setSelectedBlueprint] = useState('')
    const [image, setImage] = useState<string | null>(null)
    const [loadingImage, setLoadingImage] = useState(false)

    // Interaction State
    const [clickPos, setClickPos] = useState<{ x: number, y: number } | null>(null)
    const [showModal, setShowModal] = useState(false)
    const [actionLabel, setActionLabel] = useState('')
    const [actionType, setActionType] = useState('click')
    const [typeText, setTypeText] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const imageRef = useRef<HTMLImageElement>(null)

    const supabase = createClient()

    useEffect(() => {
        async function init() {
            const { data } = await supabase.from('blueprints').select('id, name').order('created_at', { ascending: false })
            if (data) setBlueprints(data)
        }
        init()
    }, [])

    const fetchScreenshot = async () => {
        setLoadingImage(true)
        try {
            // Fetch via Orchestrator API which handles the CORS and tunnels to Vast.ai
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';
            const res = await fetch(`${API_URL}/v1/perception/screenshot?marks=false`)
            const data = await res.json()
            setImage(`data:image/png;base64,${data.image_base64}`)
        } catch (e) {
            console.error("Failed to fetch screenshot:", e)
            alert("Failed to connect to Orchestrator API (Check backend logs)")
        }
        setLoadingImage(false)
    }

    const handleImageClick = (e: React.MouseEvent<HTMLImageElement>) => {
        if (!imageRef.current || !selectedBlueprint) return

        // Calculate click coordinates mapped relative to native 1920x1080 resolution
        const rect = imageRef.current.getBoundingClientRect()
        const scaleX = 1920 / rect.width
        const scaleY = 1080 / rect.height

        const x = Math.round((e.clientX - rect.left) * scaleX)
        const y = Math.round((e.clientY - rect.top) * scaleY)

        setClickPos({ x, y })
        setShowModal(true)
    }

    const handleCreateBlueprint = async () => {
        const name = prompt("Enter a name for the new Blueprint:")
        if (!name) return
        const { data, error } = await supabase.from('blueprints').insert({ name }).select()
        if (!error && data) {
            setBlueprints([data[0], ...blueprints])
            setSelectedBlueprint(data[0].id)
        }
    }

    const handleActionSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!clickPos || !selectedBlueprint) return

        setSubmitting(true)
        try {
            // Send the X, Y command to the Orchestrator
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';
            const res = await fetch(`${API_URL}/v1/teach/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    blueprint_id: selectedBlueprint,
                    action: actionType,
                    label: actionLabel,
                    x: clickPos.x,
                    y: clickPos.y,
                    text: typeText
                })
            })

            const data = await res.json()
            if (res.ok) {
                // Success! Reload the screenshot to capture the new DOM state
                setShowModal(false)
                setActionLabel('')
                setTypeText('')
                await fetchScreenshot()
            } else {
                alert(`API Error: ${data.detail || 'Unknown Error'}`)
            }
        } catch (e) {
            console.error(e)
            alert("Failed to connect to Orchestrator API")
        }
        setSubmitting(false)
    }

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)]">
            <div className="flex items-end justify-between mb-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Agent Studio</h1>
                    <p className="text-zinc-400 mt-2 max-w-2xl">
                        Teach the agent how to navigate. First, select or create a Blueprint.
                        Then, click <b>"Capture State"</b> to view the remote browser. Click directly on the image to record a visual action!
                    </p>
                </div>

                <div className="flex items-center gap-4 bg-zinc-900/50 p-2 rounded-xl border border-zinc-800">
                    <select
                        value={selectedBlueprint}
                        onChange={(e) => setSelectedBlueprint(e.target.value)}
                        className="bg-zinc-800 border-none text-sm text-white rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-primary w-64 appearance-none"
                    >
                        <option value="">Select Blueprint to Edit...</option>
                        {blueprints.map(bp => (
                            <option key={bp.id} value={bp.id}>{bp.name}</option>
                        ))}
                    </select>
                    <button
                        onClick={handleCreateBlueprint}
                        className="bg-zinc-800 hover:bg-zinc-700 text-white p-2 rounded-lg font-medium transition-colors border border-zinc-700"
                        title="Create New Blueprint"
                    >
                        <Plus className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div className="flex-1 glass rounded-xl border border-zinc-800 overflow-hidden flex flex-col relative">
                <div className="h-12 border-b border-zinc-800 bg-zinc-900/80 flex items-center px-4 justify-between shrink-0">
                    <div className="flex items-center text-sm font-medium text-zinc-300">
                        <Camera className="w-4 h-4 text-primary mr-2" />
                        Live Sandbox Canvas (Vast.ai)
                    </div>

                    <button
                        onClick={fetchScreenshot}
                        disabled={loadingImage}
                        className="bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 px-4 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center disabled:opacity-50"
                    >
                        {loadingImage ? <Loader2 className="w-3 h-3 animate-spin mr-2" /> : <ImageIcon className="w-3 h-3 mr-2" />}
                        Capture State
                    </button>
                </div>

                <div className="flex-1 bg-zinc-950 overflow-auto relative p-4 flex items-center justify-center">
                    {!image && !loadingImage && (
                        <div className="text-center text-zinc-500 flex flex-col items-center bg-zinc-900/50 p-8 rounded-xl border border-zinc-800 border-dashed max-w-lg">
                            <MousePointer2 className="w-12 h-12 mb-4 opacity-50 text-primary" />
                            <h3 className="text-lg font-semibold text-zinc-300 mb-2">Ready to Record</h3>
                            <div className="text-sm text-left space-y-2 mt-2">
                                <p><span className="text-primary font-bold mr-2">1.</span> Select a Blueprint from the top right dropdown.</p>
                                <p><span className="text-primary font-bold mr-2">2.</span> Click <b>"Capture State"</b> to pull the live view from Vast.ai.</p>
                                <p><span className="text-primary font-bold mr-2">3.</span> Click anywhere on the loaded image to teach the agent a new step.</p>
                            </div>
                        </div>
                    )}

                    {loadingImage && !image && (
                        <Loader2 className="w-12 h-12 text-primary animate-spin" />
                    )}

                    {image && (
                        <div className="relative inline-block border border-zinc-800 shadow-2xl rounded-sm overflow-hidden group">
                            <img
                                ref={imageRef}
                                src={image}
                                alt="Agent Screen"
                                className={`max-w-full h-auto cursor-crosshair transition-opacity ${loadingImage ? 'opacity-50' : 'opacity-100'}`}
                                onClick={handleImageClick}
                            />
                            {!selectedBlueprint && (
                                <div className="absolute inset-0 bg-black/60 flex items-center justify-center backdrop-blur-sm">
                                    <p className="bg-zinc-900 border border-zinc-700 px-4 py-2 rounded-lg text-amber-400 font-medium font-mono text-sm">
                                        ⚠ Select or Create a Blueprint first to record actions.
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Action Modal */}
            {showModal && clickPos && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="glass rounded-2xl w-full max-w-md shadow-2xl p-6 border border-zinc-700/50"
                    >
                        <h3 className="text-xl font-bold mb-1">Record Action</h3>
                        <p className="text-sm text-zinc-400 mb-6 font-mono">X: {clickPos.x} | Y: {clickPos.y} (Native)</p>

                        <form onSubmit={handleActionSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-zinc-300 mb-1">Action Type</label>
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setActionType('click')}
                                        className={`p-2 rounded-lg text-sm font-medium border transition-colors ${actionType === 'click' ? 'bg-primary/20 border-primary text-primary' : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:bg-zinc-800'}`}
                                    >
                                        Click Element
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setActionType('type')}
                                        className={`p-2 rounded-lg text-sm font-medium border transition-colors ${actionType === 'type' ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:bg-zinc-800'}`}
                                    >
                                        Click & Type
                                    </button>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-zinc-300 mb-1">Semantic Label</label>
                                <input
                                    type="text"
                                    value={actionLabel}
                                    onChange={(e) => setActionLabel(e.target.value)}
                                    placeholder="e.g., Search Input Field"
                                    required
                                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-white outline-none focus:ring-2 focus:ring-primary/50 text-sm"
                                />
                                <p className="text-xs text-zinc-500 mt-1">This label maps the visual embedding to memory.</p>
                            </div>

                            {actionType === 'type' && (
                                <div>
                                    <label className="block text-sm font-medium text-zinc-300 mb-1">Text Sequence</label>
                                    <input
                                        type="text"
                                        value={typeText}
                                        onChange={(e) => setTypeText(e.target.value)}
                                        placeholder="Enter text to type..."
                                        required
                                        className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-white outline-none focus:ring-2 focus:ring-emerald-500/50 text-sm"
                                    />
                                </div>
                            )}

                            <div className="flex gap-3 pt-4 border-t border-zinc-800">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    disabled={submitting}
                                    className="flex-1 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg px-4 py-2 font-medium transition-colors text-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={submitting || !actionLabel}
                                    className="flex-[2] bg-primary hover:bg-blue-600 disabled:opacity-50 text-white rounded-lg px-4 py-2 font-medium transition-colors text-sm flex items-center justify-center"
                                >
                                    {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <><CheckCircle className="w-4 h-4 mr-2" /> Save to Memory & Execute</>}
                                </button>
                            </div>
                        </form>
                    </motion.div>
                </div>
            )}
        </div>
    )
}
