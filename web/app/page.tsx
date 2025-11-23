'use client';

import { useState } from 'react';
import { Terminal, Shield, Power, Loader2, AlertCircle } from 'lucide-react';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [missionData, setMissionData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const startMission = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const res = await fetch('http://localhost:8000/api/containers/start', {
        method: 'POST',
      });
      
      if (!res.ok) {
        if (res.status === 429) throw new Error("RATE LIMIT EXCEEDED. WAIT.");
        throw new Error("SYSTEM ERROR: UNABLE TO DEPLOY.");
      }

      const data = await res.json();
      setMissionData(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col items-center justify-center p-4 font-mono">
      {/* Header / Identity */}
      <div className="mb-12 text-center space-y-4">
        <div className="inline-flex items-center justify-center p-3 bg-zinc-900 border border-zinc-800 rounded-full mb-4">
          <Shield className="w-8 h-8 text-emerald-500" />
        </div>
        <h1 className="text-4xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-zinc-200 to-zinc-500">
          PROJECT <span className="text-emerald-500">SOL</span>
        </h1>
        <p className="text-zinc-500 uppercase tracking-widest text-sm">
          Secure Operations Laboratory
        </p>
      </div>

      {/* Main Terminal Card */}
      <div className="w-full max-w-2xl bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden shadow-2xl shadow-black/50">
        
        {/* Terminal Header */}
        <div className="bg-zinc-950 px-4 py-2 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-zinc-500" />
            <span className="text-xs text-zinc-400">bash — agent@sol-ctf:~</span>
          </div>
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-rose-500/20 border border-rose-500/50"></div>
            <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500/50"></div>
            <div className="w-3 h-3 rounded-full bg-emerald-500/20 border border-emerald-500/50"></div>
          </div>
        </div>

        {/* Content Area */}
        <div className="p-8 min-h-[300px] flex flex-col items-center justify-center space-y-6">
          
          {!missionData ? (
            // Initial State
            <div className="text-center space-y-6 animate-in fade-in duration-500">
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-zinc-100">MISSION BRIEFING</h2>
                <p className="text-zinc-400 text-sm max-w-md mx-auto">
                  Target: Web Server (Nginx)<br/>
                  Objective: Infiltrate and retrieve the flag.<br/>
                  Threat Level: <span className="text-emerald-500">LOW</span>
                </p>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-rose-500 bg-rose-500/10 px-4 py-2 rounded border border-rose-500/20">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm font-bold">{error}</span>
                </div>
              )}

              <button
                onClick={startMission}
                disabled={isLoading}
                className="group relative inline-flex items-center gap-2 px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-zinc-950 font-bold rounded transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    DEPLOYING...
                  </>
                ) : (
                  <>
                    <Power className="w-4 h-4" />
                    INITIALIZE MISSION
                  </>
                )}
              </button>
            </div>
          ) : (
            // Success State
            <div className="w-full text-left space-y-4 animate-in zoom-in-95 duration-300">
              <div className="flex items-center gap-2 text-emerald-500 mb-4">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="font-bold tracking-wider">CONNECTION ESTABLISHED</span>
              </div>
              
              <div className="space-y-4 font-mono text-sm">
                <div className="grid grid-cols-[100px_1fr] gap-2">
                  <span className="text-zinc-500">STATUS:</span>
                  <span className="text-zinc-100">{missionData.status.toUpperCase()}</span>
                  
                  <span className="text-zinc-500">ID:</span>
                  <span className="text-zinc-100">{missionData.container_id}</span>
                  
                  <span className="text-zinc-500">TARGET:</span>
                  <a href={missionData.url} target="_blank" rel="noopener noreferrer" className="text-emerald-400 underline hover:text-emerald-300 break-all">
                    {missionData.url}
                  </a>
                </div>

                <div className="p-4 bg-zinc-950 border border-emerald-500/20 rounded text-emerald-500/80 text-xs">
                  {`> Establishing secure tunnel... OK`} <br/>
                  {`> Port forwarding ${missionData.port} -> 80... OK`} <br/>
                  {`> Target confirmed. Good luck, Agent.`}
                </div>
              </div>

              <button
                onClick={() => setMissionData(null)}
                className="text-xs text-zinc-500 hover:text-zinc-300 underline mt-4"
              >
                [ RESET CONNECTION ]
              </button>
            </div>
          )}

        </div>
      </div>
    </main>
  );
}
