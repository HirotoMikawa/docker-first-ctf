'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Terminal, Shield, Loader2, AlertCircle, LogOut, User, Target, Flag, CheckCircle2, XCircle, BookOpen, AlertTriangle } from 'lucide-react';
import { createClient } from '@/utils/supabase/client';
import { buildApiUrl } from '@/utils/api';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import type { User as SupabaseUser } from '@supabase/supabase-js';
import type { Challenge, MissionData, SubmitResult } from '@/types';
import ChallengeCard from '@/components/ChallengeCard';

export default function Home() {
  const router = useRouter();
  const supabase = createClient();
  const [isLoading, setIsLoading] = useState(false);
  const [loadingChallengeId, setLoadingChallengeId] = useState<string | null>(null);
  const [missionData, setMissionData] = useState<MissionData | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Flag提出用のState
  const [flagInput, setFlagInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<SubmitResult | null>(null);
  
  // エラーを安全に設定するヘルパー関数
  const setErrorSafe = (err: any) => {
    // nullまたはundefinedが渡された場合は、エラーをクリアする
    if (err === null || err === undefined) {
      setError(null);
      return;
    }
    
    let errorMessage: string = 'An error occurred';
    
    try {
      if (typeof err === 'string') {
        errorMessage = err;
      } else if (err instanceof Error) {
        errorMessage = err.message || String(err);
      } else if (typeof err === 'object') {
        if (err.message) {
          errorMessage = String(err.message);
        } else if (err.detail) {
          errorMessage = String(err.detail);
        } else if (err.error) {
          if (typeof err.error === 'string') {
            errorMessage = err.error;
          } else if (err.error?.message) {
            errorMessage = String(err.error.message);
          } else {
            errorMessage = JSON.stringify(err.error, null, 2);
          }
        } else {
          errorMessage = JSON.stringify(err, null, 2);
        }
      } else {
        errorMessage = String(err);
      }
    } catch (e) {
      console.error('Error in setErrorSafe:', e);
      errorMessage = 'Failed to process error message';
    }
    
    console.log('Setting error message:', errorMessage);
    setError(errorMessage);
  };
  const [user, setUser] = useState<SupabaseUser | null>(null);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [loadingChallenges, setLoadingChallenges] = useState(true);
  
  // Writeup Dialog state
  const [selectedWriteup, setSelectedWriteup] = useState<string | null>(null);
  const [showWriteupDialog, setShowWriteupDialog] = useState(false);
  const [showWriteupConfirm, setShowWriteupConfirm] = useState(false);

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

    // 問題一覧を取得
    const fetchChallenges = async () => {
      try {
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        if (sessionError) {
          console.error('Session error:', sessionError);
          const errorMsg = sessionError?.message || sessionError?.error_description || JSON.stringify(sessionError);
          setErrorSafe(`Authentication error: ${errorMsg}`);
          setLoadingChallenges(false);
          return;
        }

        if (!session) {
          console.error('No session found');
          setErrorSafe('Please login to view challenges');
          setLoadingChallenges(false);
          return;
        }

        if (!session.access_token) {
          console.error('No access token in session');
          setErrorSafe('Invalid session: missing access token');
          setLoadingChallenges(false);
          return;
        }

        console.log('Fetching challenges with token:', session.access_token.substring(0, 20) + '...');

        const apiUrl = buildApiUrl('/api/challenges');
        const res = await fetch(apiUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        });

        console.log('Response status:', res.status, res.statusText);

        if (!res.ok) {
          const errorText = await res.text();
          let errorMessage = `Failed to fetch challenges (${res.status})`;
          
          try {
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson.detail || errorMessage;
          } catch {
            errorMessage = errorText || errorMessage;
          }
          
          console.error('API error:', errorMessage);
          throw new Error(errorMessage);
        }

        let data;
        try {
          data = await res.json();
        } catch (jsonError: any) {
          console.error('JSON parse error:', jsonError);
          throw new Error('Invalid JSON response from server');
        }
        
        console.log('Challenges loaded:', data?.length || 0);
        console.log('Challenges data:', JSON.stringify(data, null, 2));
        
        // データの構造を確認し、必要に応じて変換
        if (data && Array.isArray(data)) {
          const normalizedChallenges = data.map((challenge: any) => {
            // challenge_idが存在しない場合、idから取得
            if (!challenge.challenge_id && challenge.id) {
              challenge.challenge_id = challenge.id;
            }
            console.log('Normalized challenge:', challenge);
            return challenge;
          });
          setChallenges(normalizedChallenges);
        } else {
          setChallenges([]);
        }
        setError(null); // 成功時はエラーをクリア
      } catch (err: any) {
        console.error('Failed to fetch challenges:', err);
        // エラーオブジェクトを適切に文字列に変換（より堅牢に）
        let errorMessage = 'Failed to load challenges';
        
        try {
          if (err instanceof Error) {
            errorMessage = err.message || String(err);
          } else if (typeof err === 'string') {
            errorMessage = err;
          } else if (err && typeof err === 'object') {
            if (err.message) {
              errorMessage = String(err.message);
            } else if (err.detail) {
              errorMessage = String(err.detail);
            } else {
              errorMessage = JSON.stringify(err, null, 2);
            }
          } else {
            errorMessage = String(err);
          }
        } catch (stringifyError) {
          errorMessage = 'Failed to load challenges';
          console.error('Failed to stringify error:', stringifyError);
        }
        
        // 確実に文字列として設定
        setErrorSafe(errorMessage);
      } finally {
        setLoadingChallenges(false);
      }
    };

    fetchChallenges();

    return () => subscription.unsubscribe();
  }, [supabase]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push('/login');
    router.refresh();
  };

  const startMission = async (challengeId: string) => {
    console.log("Starting mission with ID:", challengeId);
    console.log("Challenge ID type:", typeof challengeId);
    console.log("Challenge ID value:", challengeId);
    
    setIsLoading(true);
    setLoadingChallengeId(challengeId);
    setError(null);
    
    try {
      // challengeIdの検証（最初にチェック）
      if (!challengeId || challengeId.trim() === '') {
        console.error('Challenge ID validation failed:', challengeId);
        throw new Error('Challenge ID is required');
      }
      
      // JWTトークンを取得
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        throw new Error("Authentication required. Please login.");
      }
      
      // リクエストボディを構築（キー名は必ず challenge_id）
      const requestBody = { challenge_id: String(challengeId).trim() };
      console.log('Sending request body:', requestBody);
      console.log('Stringified body:', JSON.stringify(requestBody));
      
      const apiUrl = buildApiUrl('/api/containers/start');
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        let errorMessage = "SYSTEM ERROR: UNABLE TO DEPLOY.";
        
        try {
          const errorJson = JSON.parse(errorText);
          // 422エラーの場合、詳細なバリデーションエラーを表示
          if (res.status === 422 && errorJson.errors) {
            const validationErrors = errorJson.errors.map((err: any) => 
              `${err.field}: ${err.message}`
            ).join('; ');
            errorMessage = `Validation Error: ${validationErrors}`;
          } else {
            errorMessage = errorJson.detail || errorJson.message || errorMessage;
          }
        } catch {
          errorMessage = errorText || errorMessage;
        }
        
        if (res.status === 429) {
          throw new Error("RATE LIMIT EXCEEDED. WAIT.");
        } else if (res.status === 404) {
          throw new Error("CHALLENGE NOT FOUND.");
        } else if (res.status === 422) {
          throw new Error(errorMessage);
        } else {
          throw new Error(errorMessage);
        }
      }

      let data;
      try {
        data = await res.json();
      } catch (jsonError: any) {
        console.error('JSON parse error:', jsonError);
        throw new Error('Invalid response from server');
      }
      
      // challenge_idを追加して保存（Flag提出時に必要）
      setMissionData({ ...data, challenge_id: challengeId });
      // Flag提出関連のStateをリセット
      setFlagInput('');
      setSubmitResult(null);
    } catch (err: any) {
      console.error('Mission start error:', err);
      console.error('Error type:', typeof err);
      console.error('Error details:', err);
      
      // エラーオブジェクトを適切に文字列に変換（より堅牢に）
      let errorMessage = 'SYSTEM ERROR: UNABLE TO DEPLOY.';
      
      try {
        if (err instanceof Error) {
          errorMessage = err.message || String(err);
        } else if (typeof err === 'string') {
          errorMessage = err;
        } else if (err && typeof err === 'object') {
          // オブジェクトの場合、可能な限り詳細を抽出
          if (err.message) {
            errorMessage = String(err.message);
          } else if (err.detail) {
            errorMessage = String(err.detail);
          } else if (err.error) {
            if (typeof err.error === 'string') {
              errorMessage = err.error;
            } else if (err.error?.message) {
              errorMessage = String(err.error.message);
            } else {
              errorMessage = JSON.stringify(err.error);
            }
          } else {
            // 最後の手段: JSON文字列化
            errorMessage = JSON.stringify(err, null, 2);
          }
        } else {
          errorMessage = String(err);
        }
      } catch (stringifyError) {
        // 文字列化に失敗した場合
        errorMessage = 'Unknown error occurred';
        console.error('Failed to stringify error:', stringifyError);
      }
      
        // 確実に文字列として設定
        setErrorSafe(errorMessage);
    } finally {
      setIsLoading(false);
      setLoadingChallengeId(null);
    }
  };

  // Flag提出機能
  const submitFlag = async () => {
    if (!missionData || !flagInput || !missionData.challenge_id) {
      setErrorSafe('Mission is not active or challenge ID is missing');
      return;
    }

    // エラーをクリア（前のエラーを消去）
    setError(null);
    setIsSubmitting(true);
    setSubmitResult(null);

    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        throw new Error("Session expired. Please login again.");
      }

      const apiUrl = buildApiUrl('/api/challenges/submit');
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          challenge_id: missionData.challenge_id,
          flag_submission: flagInput.trim(),
        }),
      });

      // レスポンスが成功（200 OK）の場合、エラーを設定しない
      if (res.ok) {
        const result = await res.json();
        setSubmitResult(result);
        // 成功時はエラーを設定しない（setErrorは呼ばない）
      } else {
        // レスポンスがエラーの場合のみ、エラーを設定
        const errorText = await res.text();
        let errorMessage = "Submission failed";
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorMessage;
        } catch {
          errorMessage = errorText || errorMessage;
        }
        setErrorSafe(errorMessage);
        setSubmitResult({
          correct: false,
          message: `ERROR: ${errorMessage}`
        });
      }
    } catch (err: any) {
      // ネットワークエラーなどの例外の場合のみ、エラーを設定
      console.error('Flag submission error:', err);
      setErrorSafe(err.message || 'Submission failed');
      setSubmitResult({
        correct: false,
        message: `ERROR: ${err.message || 'Submission failed'}`
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getDifficultyColor = (difficulty?: number) => {
    // Handle numeric difficulty (1-5)
    if (typeof difficulty === 'number') {
      if (difficulty <= 1) return 'text-emerald-500';
      if (difficulty <= 2) return 'text-amber-500';
      if (difficulty <= 3) return 'text-orange-500';
      if (difficulty <= 4) return 'text-rose-500';
      return 'text-rose-600'; // difficulty 5
    }
    
    // Default for undefined/null
    return 'text-zinc-400';
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 p-4 font-mono">
      {/* Header / Identity */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="text-center space-y-4 mb-8">
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
          <div className="mb-6 bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex items-center justify-between">
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

        {/* Error Message */}
        {error && (
          <div className="mb-6 flex items-center gap-2 text-rose-500 bg-rose-500/10 px-4 py-3 rounded-lg border border-rose-500/20">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm font-bold">
              {(() => {
                try {
                  if (error === null || error === undefined) {
                    return 'Unknown error';
                  }
                  if (typeof error === 'string') {
                    return error;
                  }
                  if (typeof error === 'object') {
                    const errorStr = JSON.stringify(error, null, 2);
                    return errorStr.length > 200 ? errorStr.substring(0, 200) + '...' : errorStr;
                  }
                  return String(error);
                } catch (e) {
                  return 'Error displaying error message';
                }
              })()}
            </span>
          </div>
        )}

        {/* Mission Active State */}
        {missionData ? (
          <div className="w-full bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden shadow-2xl shadow-black/50">
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
            <div className="p-8 space-y-4 animate-in zoom-in-95 duration-300">
              <div className="flex items-center gap-2 text-emerald-500 mb-4">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="font-bold tracking-wider">CONNECTION ESTABLISHED</span>
              </div>
              
              <div className="space-y-4 font-mono text-sm">
                <div className="grid grid-cols-[120px_1fr] gap-2">
                  <span className="text-zinc-500">MISSION:</span>
                  <span className="text-zinc-100 font-bold">{missionData.challenge_name || 'Unknown'}</span>
                  
                  <span className="text-zinc-500">STATUS:</span>
                  <span className="text-zinc-100">{missionData.status.toUpperCase()}</span>
                  
                  <span className="text-zinc-500">ID:</span>
                  <span className="text-zinc-100 font-mono">{missionData.container_id}</span>
                  
                  <span className="text-zinc-500">TARGET:</span>
                  <a 
                    href={missionData.url} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="text-emerald-400 underline hover:text-emerald-300 break-all"
                  >
                    {missionData.url}
                  </a>
                </div>

                <div className="p-4 bg-zinc-950 border border-emerald-500/20 rounded text-emerald-500/80 text-xs">
                  {`> Establishing secure tunnel... OK`} <br/>
                  {`> Port forwarding ${missionData.port} -> ${missionData.port}... OK`} <br/>
                  {`> Target confirmed. Good luck, Agent.`}
                </div>
              </div>

              {/* Flag Submission Form */}
              <div className="space-y-3 border-t border-zinc-800 pt-4">
                <div className="flex items-center gap-2 text-zinc-400 text-xs uppercase tracking-widest">
                  <Flag className="w-4 h-4" />
                  <span>Submit Flag</span>
                </div>
                <div className="flex gap-2">
                  <div className="relative flex-grow">
                    <input
                      type="text"
                      value={flagInput}
                      onChange={(e) => setFlagInput(e.target.value)}
                      placeholder="SolCTF{...}"
                      className="w-full bg-zinc-950 border border-zinc-700 rounded px-4 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all font-mono"
                      disabled={isSubmitting}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !isSubmitting && flagInput.trim()) {
                          submitFlag();
                        }
                      }}
                    />
                  </div>
                  <Button
                    onClick={submitFlag}
                    disabled={isSubmitting || !flagInput.trim()}
                    className="px-6 bg-emerald-600 hover:bg-emerald-700 text-white font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        VERIFYING...
                      </>
                    ) : (
                      'SUBMIT'
                    )}
                  </Button>
                </div>
              </div>

              {/* Submission Result */}
              {submitResult && (
                <div className={`p-4 rounded border flex items-center gap-3 animate-in slide-in-from-top-2 ${
                  submitResult.correct
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                }`}>
                  {submitResult.correct ? (
                    <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 flex-shrink-0" />
                  )}
                  <span className="text-sm font-bold tracking-wide">{submitResult.message}</span>
                </div>
              )}

              {/* Writeup Button - Show after INITIALIZE */}
              {(() => {
                // Find the current challenge's writeup
                const currentChallenge = challenges.find(
                  (c) => c.challenge_id === missionData?.challenge_id || c.id === missionData?.challenge_id
                );
                
                if (currentChallenge?.writeup && missionData) {
                  return (
                    <div className="border-t border-zinc-800 pt-4">
                      <Button
                        onClick={() => {
                          // Replace {{CONTAINER_HOST}} placeholder with actual container URL
                          let writeup = currentChallenge.writeup || null;
                          if (writeup && missionData && missionData.url) {
                            // Extract hostname from missionData.url (e.g., "http://localhost:32804" -> "localhost:32804")
                            const url = new URL(missionData.url);
                            const containerHost = `${url.hostname}${url.port ? ':' + url.port : ''}`;
                            // Replace {{CONTAINER_HOST}} with actual host:port
                            writeup = writeup.replace(/\{\{CONTAINER_HOST\}\}/g, containerHost);
                            // Also replace http://localhost:8000 or similar patterns if they exist
                            writeup = writeup.replace(/http:\/\/localhost:8000/g, missionData.url);
                            writeup = writeup.replace(/http:\/\/localhost:\d+/g, missionData.url);
                          }
                          setSelectedWriteup(writeup);
                          setShowWriteupConfirm(true);
                        }}
                        variant="outline"
                        size="lg"
                        className="w-full border-emerald-500/50 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400"
                      >
                        <BookOpen className="w-5 h-5 mr-2" />
                        📘 解説を読む
                      </Button>
                    </div>
                  );
                }
                return null;
              })()}

              <Button
                onClick={() => {
                  setMissionData(null);
                  setFlagInput('');
                  setSubmitResult(null);
                }}
                variant="outline"
                className="w-full border-zinc-700 hover:bg-zinc-800"
              >
                [ RESET CONNECTION ]
              </Button>
            </div>
          </div>
        ) : (
          /* Challenges Grid */
          <div>
            <div className="mb-6 flex items-center gap-2">
              <Target className="w-5 h-5 text-emerald-500" />
              <h2 className="text-xl font-bold text-zinc-100">AVAILABLE MISSIONS</h2>
            </div>

            {loadingChallenges ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
                <span className="ml-2 text-zinc-400">Loading missions...</span>
              </div>
            ) : challenges.length === 0 ? (
              <div className="text-center py-12 text-zinc-400">
                <p>No missions available.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {challenges.map((challenge) => (
                  <ChallengeCard
                    key={challenge.challenge_id}
                    challenge={challenge}
                    onInitialize={startMission}
                    isLoading={isLoading}
                    loadingChallengeId={loadingChallengeId}
                    getDifficultyColor={getDifficultyColor}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Writeup Confirmation Dialog */}
      <Dialog open={showWriteupConfirm} onOpenChange={setShowWriteupConfirm}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
              解説を表示しますか？
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              この解説には問題の解法が含まれています。表示してもよろしいですか？
            </DialogDescription>
          </DialogHeader>
          <div className="flex gap-2 justify-end mt-4">
            <Button
              variant="outline"
              onClick={() => {
                setShowWriteupConfirm(false);
                setSelectedWriteup(null);
              }}
            >
              キャンセル
            </Button>
            <Button
              onClick={() => {
                setShowWriteupConfirm(false);
                setShowWriteupDialog(true);
              }}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              解説を表示
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Writeup Display Dialog */}
      <Dialog open={showWriteupDialog} onOpenChange={setShowWriteupDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-zinc-100">
              <BookOpen className="w-5 h-5 text-emerald-400" />
              解説記事
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              問題の解法と解説ガイド
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 prose prose-invert prose-zinc max-w-none">
            {selectedWriteup ? (
              <div className="text-zinc-300">
                {renderMarkdown(selectedWriteup)}
              </div>
            ) : (
              <p className="text-zinc-400">解説が利用できません。</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </main>
  );
}

// Simple Markdown renderer (basic support)
function renderMarkdown(markdown: string): React.ReactNode {
  const lines = markdown.split('\n');
  const elements: React.ReactNode[] = [];
  let currentParagraph: string[] = [];
  let inCodeBlock = false;
  let codeBlockContent: string[] = [];
  let currentListItems: string[] = [];
  let inList = false;

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      const text = currentParagraph.join(' ');
      if (text.trim()) {
        // Simple markdown parsing
        const processed = text
          .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-zinc-100">$1</strong>')
          .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
          .replace(/`(.*?)`/g, '<code class="bg-zinc-800 px-1 py-0.5 rounded text-emerald-400">$1</code>');
        
        elements.push(
          <p 
            key={`p-${elements.length}`}
            className="mb-3 text-zinc-300"
            dangerouslySetInnerHTML={{ __html: processed }}
          />
        );
      }
      currentParagraph = [];
    }
  };

  const flushList = () => {
    if (currentListItems.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="ml-6 mb-4 list-disc space-y-1">
          {currentListItems.map((item, idx) => {
            const processed = item
              .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-zinc-100">$1</strong>')
              .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
              .replace(/`(.*?)`/g, '<code class="bg-zinc-800 px-1 py-0.5 rounded text-emerald-400">$1</code>');
            return (
              <li 
                key={idx}
                className="text-zinc-300"
                dangerouslySetInnerHTML={{ __html: processed }}
              />
            );
          })}
        </ul>
      );
      currentListItems = [];
      inList = false;
    }
  };

  lines.forEach((line, index) => {
    // Code block detection
    if (line.startsWith('```')) {
      flushParagraph();
      flushList();
      if (inCodeBlock) {
        // End code block
        elements.push(
          <pre key={`code-${elements.length}`} className="bg-zinc-900 border border-zinc-800 rounded p-4 overflow-x-auto mb-4">
            <code className="text-emerald-400 text-xs font-mono whitespace-pre">{codeBlockContent.join('\n')}</code>
          </pre>
        );
        codeBlockContent = [];
        inCodeBlock = false;
      } else {
        // Start code block
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line);
      return;
    }

    // Header detection
    if (line.startsWith('### ')) {
      flushParagraph();
      flushList();
      const text = line.substring(4);
      elements.push(
        <h3 key={`h3-${elements.length}`} className="text-xl font-bold text-zinc-100 mt-6 mb-3">
          {text}
        </h3>
      );
      return;
    }
    if (line.startsWith('## ')) {
      flushParagraph();
      flushList();
      const text = line.substring(3);
      elements.push(
        <h2 key={`h2-${elements.length}`} className="text-2xl font-bold text-zinc-100 mt-8 mb-4">
          {text}
        </h2>
      );
      return;
    }
    if (line.startsWith('# ')) {
      flushParagraph();
      flushList();
      const text = line.substring(2);
      elements.push(
        <h1 key={`h1-${elements.length}`} className="text-3xl font-bold text-zinc-100 mt-10 mb-5">
          {text}
        </h1>
      );
      return;
    }

    // List detection
    if (line.match(/^[-*] /) || line.match(/^\d+\. /)) {
      flushParagraph();
      const listItem = line.replace(/^[-*] /, '').replace(/^\d+\. /, '');
      currentListItems.push(listItem);
      inList = true;
      return;
    }

    // Empty line
    if (line.trim() === '') {
      flushParagraph();
      flushList();
      return;
    }

    // Regular line
    if (inList) {
      flushList();
    }
    currentParagraph.push(line);
  });

  flushParagraph();
  flushList();

  return <div className="space-y-2">{elements}</div>;
}
