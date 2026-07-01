export const FEATURE_KEYS = [
  'years_experience_fit', 'title_trajectory_score', 'production_ml_evidence_score', 
  'domain_adjacency_penalty', 'consulting_only_penalty', 'research_only_disqualifier', 
  'role_relevance_score', 'skill_semantic_match', 'bm25_score', 'skill_trust_score', 
  'framework_enthusiast_penalty', 'education_tier_score', 'availability_score', 
  'notice_period_fit', 'verification_trust_score', 'location_boost', 'honeypot_suspicion_score',
  'job_hopper_penalty', 'overqualified_penalty', 'non_coder_penalty', 'loyalty_boost', 'recent_ml_focus'
];

export const FEATURE_COLORS: Record<string, string> = {
  'years_experience_fit': 'bg-[#3B82F6]',
  'title_trajectory_score': 'bg-[#6366F1]',
  'production_ml_evidence_score': 'bg-[#8B5CF6]',
  'domain_adjacency_penalty': 'bg-[#F43F5E]',
  'consulting_only_penalty': 'bg-[#F97316]',
  'research_only_disqualifier': 'bg-[#EF4444]',
  'role_relevance_score': 'bg-[#10B981]',
  'skill_semantic_match': 'bg-[#059669]',
  'bm25_score': 'bg-[#14B8A6]',
  'skill_trust_score': 'bg-[#06B6D4]',
  'framework_enthusiast_penalty': 'bg-[#EAB308]',
  'education_tier_score': 'bg-[#0EA5E9]',
  'availability_score': 'bg-[#84CC16]',
  'notice_period_fit': 'bg-[#22C55E]',
  'verification_trust_score': 'bg-[#60A5FA]',
  'location_boost': 'bg-[#A855F7]',
  'honeypot_suspicion_score': 'bg-[#DC2626]',
  'job_hopper_penalty': 'bg-[#B91C1C]',
  'overqualified_penalty': 'bg-[#991B1B]',
  'non_coder_penalty': 'bg-[#7F1D1D]',
  'loyalty_boost': 'bg-[#2DD4BF]',
  'recent_ml_focus': 'bg-[#06B6D4]'
};

export const formatFeatureName = (key: string) => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};
