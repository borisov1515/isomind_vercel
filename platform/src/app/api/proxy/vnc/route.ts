import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
    const ORCHESTRATOR_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8003";

    try {
        const response = await fetch(`${ORCHESTRATOR_URL}/v1/dashboard/vnc`);

        if (!response.ok) {
            return new NextResponse("VNC Stream not available", { status: 502 });
        }

        const html = await response.text();
        return new NextResponse(html, {
            headers: {
                "Content-Type": "text/html",
                "Cache-Control": "no-store, no-cache, must-revalidate",
            }
        });
    } catch (error) {
        console.error("VNC Proxy Error:", error);
        return new NextResponse("Failed to connect to Orchestrator", { status: 500 });
    }
}
