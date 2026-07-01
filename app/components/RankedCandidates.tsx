import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, FileText, CheckCircle, AlertTriangle, Shield, TrendingUp, Search } from 'lucide-react';

interface CandidateRank {
    candidate_id: string;
    rank: number;
    score: number;
    reasoning: string;
    name: string;
    title: string;
    company: string;
}

export default function RankedCandidates() {
    const [candidates, setCandidates] = useState<CandidateRank[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchCandidates = async () => {
            try {
                const response = await fetch('/ranked_candidates.json');
                if (!response.ok) {
                    throw new Error('Failed to load ranked_candidates.json');
                }
                const data = await response.json();
                setCandidates(data);
            } catch (err: any) {
                setError(err.message);
                // Fallback mock data if the JSON is not generated yet during dev
                setCandidates([
                    {
                        candidate_id: "CAND_MOCK1",
                        rank: 1,
                        score: 0.95,
                        name: "Alex Dev",
                        title: "Senior AI Engineer",
                        company: "Tech Corp",
                        reasoning: "Top candidate based on production embeddings/retrieval experience. Brings 6.0 years of experience currently as Senior AI Engineer, leveraging Python and Weaviate."
                    },
                    {
                        candidate_id: "CAND_MOCK2",
                        rank: 2,
                        score: 0.85,
                        name: "Sam Backend",
                        title: "Backend Engineer",
                        company: "Startup Inc",
                        reasoning: "Solid candidate with 5.0 years as a Backend Engineer matching our need for strong python and ML toolset (skills: Python and Elasticsearch); however, notice period is 60 days (above JD preference)."
                    },
                    {
                        candidate_id: "CAND_MOCK3",
                        rank: 3,
                        score: 0.45,
                        name: "Casey Consultant",
                        title: "IT Consultant",
                        company: "TCS",
                        reasoning: "Lower confidence match. Profile shows 3.0 years as a IT Consultant with general engineering."
                    }
                ]);
            } finally {
                setLoading(false);
            }
        };

        fetchCandidates();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
            <header className="mb-8">
                <h1 className="text-3xl font-display font-bold text-slate-900 flex items-center gap-3">
                    <Users className="text-blue-600" size={32} />
                    Candidate Intelligence
                </h1>
                <p className="text-slate-500 mt-2">Ranked pipeline results based on engine feature evaluation.</p>
            </header>

            {error && (
                <div className="bg-orange-50 border border-orange-200 text-orange-800 p-4 rounded-xl flex items-start gap-3">
                    <AlertTriangle className="mt-0.5 flex-shrink-0 text-orange-500" />
                    <div>
                        <p className="font-semibold">Could not load actual JSON artifact</p>
                        <p className="text-sm mt-1">Showing mock data. Run `python engine/rank.py` to generate the real ranked_candidates.json.</p>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 gap-4">
                {candidates.map((cand) => (
                    <motion.div 
                        key={cand.candidate_id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden"
                    >
                        {/* Rank Badge */}
                        <div className={`absolute top-0 right-0 px-4 py-2 rounded-bl-2xl font-bold text-lg 
                            ${cand.rank <= 10 ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'}`}>
                            #{cand.rank}
                        </div>

                        <div className="flex items-start gap-6">
                            <div className="flex-1">
                                <h3 className="text-xl font-bold text-slate-900">{cand.name}</h3>
                                <div className="text-sm text-slate-500 mt-1 font-medium">{cand.title} • {cand.company}</div>
                                
                                <div className="mt-4 bg-blue-50/50 border border-blue-100 p-4 rounded-xl">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Shield size={16} className="text-blue-600" />
                                        <span className="font-semibold text-sm text-slate-700">AI Reasoning</span>
                                    </div>
                                    <p className="text-slate-700 text-sm leading-relaxed">
                                        {cand.reasoning}
                                    </p>
                                </div>
                            </div>
                            
                            <div className="w-32 flex flex-col items-center justify-center p-4 bg-slate-50 rounded-xl border border-slate-100 mt-8">
                                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Score</span>
                                <span className="text-2xl font-display font-bold text-blue-600">
                                    {(cand.score * 100).toFixed(1)}
                                </span>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
