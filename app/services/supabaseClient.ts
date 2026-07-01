import { createClient } from '@supabase/supabase-js';

// Credentials provided for this environment
const PROVIDED_SUPABASE_URL = "https://wkuibwcapqoacngfbrdp.supabase.co";
const PROVIDED_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndrdWlid2NhcHFvYWNuZ2ZicmRwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI4Njk1NDUsImV4cCI6MjA5ODQ0NTU0NX0.3lRXq8n8GH_EUkBw004S-GReA9qD7tzEOGxaQE6zD34";

// Helper to safely get env vars
const getEnvVar = (key: string): string => {
  // Try import.meta.env first (Vite standard)
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env[key]) {
    return import.meta.env[key];
  }
  
  // Fallback to empty string
  return '';
};

// Try to get from env, otherwise use provided fallback
const envUrl = getEnvVar('VITE_SUPABASE_URL');
const envKey = getEnvVar('VITE_SUPABASE_ANON_KEY');

const supabaseUrl = envUrl || PROVIDED_SUPABASE_URL;
const supabaseAnonKey = envKey || PROVIDED_SUPABASE_KEY;

console.log('Supabase initialized:', {
  url: supabaseUrl.substring(0, 30) + '...',
  hasKey: !!supabaseAnonKey
});

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    flowType: 'pkce'
  }
});
