'use client';

import { Power, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { Challenge } from '@/types';

interface ChallengeCardProps {
  challenge: Challenge;
  onInitialize: (challengeId: string) => void;
  isLoading?: boolean;
  loadingChallengeId?: string | null;
  getDifficultyColor?: (difficulty?: number) => string;
}

export default function ChallengeCard({
  challenge,
  onInitialize,
  isLoading = false,
  loadingChallengeId = null,
  getDifficultyColor,
}: ChallengeCardProps) {

  // Get tags from challenge.tags or challenge.metadata.tags
  const tags = challenge.tags || challenge.metadata?.tags || [];

  // Default difficulty color function if not provided
  const defaultGetDifficultyColor = (difficulty?: number) => {
    if (typeof difficulty === 'number') {
      if (difficulty <= 1) return 'text-emerald-500';
      if (difficulty <= 2) return 'text-amber-500';
      if (difficulty <= 3) return 'text-orange-500';
      if (difficulty <= 4) return 'text-rose-500';
      return 'text-rose-600'; // difficulty 5
    }
    return 'text-zinc-400';
  };

  const difficultyColor = (getDifficultyColor || defaultGetDifficultyColor)(challenge.difficulty);

  const handleInitialize = () => {
    const idToUse = challenge.challenge_id || (challenge as any).id;
    if (idToUse) {
      onInitialize(idToUse);
    }
  };

  const isThisChallengeLoading = isLoading && loadingChallengeId === challenge.challenge_id;

  return (
    <>
      <Card className="border-zinc-800 bg-zinc-900 hover:border-zinc-700 transition-colors">
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className="text-lg text-zinc-100">
              {challenge.title}
            </CardTitle>
            {challenge.difficulty !== undefined && (
              <span className={`text-xs font-bold uppercase px-2 py-1 rounded ${difficultyColor} bg-zinc-800`}>
                {challenge.difficulty}
              </span>
            )}
          </div>
          {challenge.category && (
            <span className="text-xs text-zinc-500 uppercase tracking-wider">
              {challenge.category}
            </span>
          )}
        </CardHeader>
        <CardContent>
          <CardDescription className="text-zinc-400 text-sm">
            {challenge.description || 'No description available.'}
          </CardDescription>
          {/* Tags Display */}
          {tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {tags.map((tag, idx) => (
                <span
                  key={idx}
                  className="text-xs px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-zinc-400 font-mono"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-2">
          <Button
            onClick={handleInitialize}
            disabled={isLoading}
            className="w-full"
            size="lg"
          >
            {isThisChallengeLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                DEPLOYING...
              </>
            ) : (
              <>
                <Power className="w-4 h-4 mr-2" />
                INITIALIZE
              </>
            )}
          </Button>
        </CardFooter>
      </Card>
    </>
  );
}

