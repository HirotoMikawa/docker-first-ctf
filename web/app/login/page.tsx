'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, Mail, Lock, Loader2, AlertCircle } from 'lucide-react';
import { createClient } from '@/utils/supabase/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
  const router = useRouter();
  const supabase = createClient();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (error) throw error;
      
      // ログイン成功後、トップページにリダイレクト
      router.push('/');
      router.refresh();
    } catch (err: any) {
      setError(err.message || 'ログインに失敗しました');
      setIsLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // ゲストアカウントの認証情報（環境変数から取得、デフォルトあり）
      const guestEmail = process.env.NEXT_PUBLIC_GUEST_EMAIL || 'guest@sol-ctf.local';
      const guestPassword = process.env.NEXT_PUBLIC_GUEST_PASSWORD || 'guest123';
      
      const { error } = await supabase.auth.signInWithPassword({
        email: guestEmail,
        password: guestPassword,
      });
      
      if (error) {
        // ゲストユーザーが存在しない場合、自動作成を試みる
        const { error: signUpError } = await supabase.auth.signUp({
          email: guestEmail,
          password: guestPassword,
          options: {
            data: {
              display_name: 'Guest User',
            },
          },
        });
        
        if (signUpError) throw signUpError;
        
        // 作成後、再度ログイン
        const { error: retryError } = await supabase.auth.signInWithPassword({
          email: guestEmail,
          password: guestPassword,
        });
        
        if (retryError) throw retryError;
      }
      
      // ログイン成功後、トップページにリダイレクト
      router.push('/');
      router.refresh();
    } catch (err: any) {
      setError(err.message || 'ゲストログインに失敗しました');
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col items-center justify-center p-4 font-mono">
      {/* Header / Identity */}
      <div className="mb-8 text-center space-y-4">
        <div className="inline-flex items-center justify-center p-3 bg-zinc-900 border border-zinc-800 rounded-full mb-4">
          <Shield className="w-8 h-8 text-emerald-500" />
        </div>
        <h1 className="text-4xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-zinc-200 to-zinc-500">
          PROJECT <span className="text-emerald-500">SOL</span>
        </h1>
        <p className="text-zinc-500 uppercase tracking-widest text-sm">
          Agent Authentication Required
        </p>
      </div>

      {/* Login Card */}
      <Card className="w-full max-w-md border-zinc-800 bg-zinc-900/95 backdrop-blur-sm">
        <CardHeader className="space-y-1 border-b border-zinc-800">
          <CardTitle className="text-2xl font-bold text-zinc-100">
            ACCESS GRANTED
          </CardTitle>
          <CardDescription className="text-zinc-400">
            セキュリティエージェントとして認証してください
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6 space-y-4">
          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 text-rose-500 bg-rose-500/10 px-4 py-2 rounded border border-rose-500/20">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm font-bold">{error}</span>
            </div>
          )}

          {/* Email Login Form */}
          <form onSubmit={handleEmailLogin} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                <Mail className="w-4 h-4" />
                EMAIL ADDRESS
              </label>
              <Input
                id="email"
                type="email"
                placeholder="agent@sol-ctf.local"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                className="font-mono"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                <Lock className="w-4 h-4" />
                PASSWORD
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                className="font-mono"
              />
            </div>
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  AUTHENTICATING...
                </>
              ) : (
                <>
                  <Shield className="w-4 h-4 mr-2" />
                  INITIALIZE SESSION
                </>
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-zinc-800" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-zinc-900 px-2 text-zinc-500">または</span>
            </div>
          </div>

          {/* Guest Login Button */}
          <Button
            type="button"
            onClick={handleGuestLogin}
            disabled={isLoading}
            variant="outline"
            className="w-full border-emerald-500/20 text-emerald-500 hover:bg-emerald-500/10 hover:border-emerald-500/40"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                GUEST MODE...
              </>
            ) : (
              <>
                <Shield className="w-4 h-4 mr-2" />
                ゲストとして始める
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Footer */}
      <p className="mt-8 text-xs text-zinc-500 text-center">
        Secure Operations Laboratory © 2024
      </p>
    </main>
  );
}

