'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Terminal, Shield, Power, Loader2, AlertCircle, LogOut, User } from 'lucide-react';
import { createClient } from '@/utils/supabase/client';
import { Button } from '@/components/ui/button';
import type { User as SupabaseUser } from '@supabase/supabase-js';

export default function Home() {
  const router = useRouter();
  const supabase = createClient();
  const [isLoading, setIsLoading] = useState(false);
  const [missionData, setMissionData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<SupabaseUser | null>(null);

  useEffect(() => {
    // ユーザー情報を取得
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setUser(user);
    };
    getUser();

    // 認証状態の変更を監視
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, [supabase]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push('/login');
    router.refresh();
  };

  const startMission = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // JWTトークンを取得
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        throw new Error("Authentication required. Please login.");
      }
      
      const res = await fetch('http://localhost:8000/api/containers/start', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
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

      {/* User Info Card */}
      {user && (
        <div className="mb-6 w-full max-w-2xl bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center">
              <User className="w-5 h-5 text-emerald-500" />
            </div>
            <div>
              <p className="text-sm font-bold text-zinc-100">
                AGENT: {user.email || user.user_metadata?.full_name || 'Unknown'}
              </p>
              <p className="text-xs text-zinc-500 font-mono">
                ID: {user.id.substring(0, 8)}...
              </p>
            </div>
          </div>
          <Button
            onClick={handleLogout}
            variant="outline"
            size="sm"
            className="border-zinc-700 hover:bg-zinc-800"
          >
            <LogOut className="w-4 h-4 mr-2" />
            LOGOUT
          </Button>
        </div>
      )}

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

              <Button
                onClick={startMission}
                disabled={isLoading}
                size="lg"
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
              </Button>
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


