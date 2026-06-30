import Groq from "groq-sdk";
import { AgentType, CourseRecommendation, ScannerCriteria, Candidate } from "../types";
import { AGENT_SYSTEM_INSTRUCTIONS } from "../constants";
import * as pdfjsLib from 'pdfjs-dist';

// Set worker to CDN to avoid Vite build issues
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

const getApiKey = () => {
  if (import.meta.env.VITE_GROQ_API_KEY) {
    return import.meta.env.VITE_GROQ_API_KEY;
  }
  console.error("No Groq API key found in environment variables");
  return "";
};

const groq = new Groq({ apiKey: getApiKey(), dangerouslyAllowBrowser: true });
const MODEL_ID = 'llama-3.3-70b-versatile'; 
const REQUESTED_MODEL_ID = 'llama-3.3-70b-versatile'; 

export const generateAgentResponse = async (
  message: string,
  agentType: AgentType,
  history: { role: 'user' | 'model'; content: string }[]
): Promise<string> => {
  try {
    const formattedHistory = history.map(h => ({
      role: h.role === 'model' ? 'assistant' : 'user',
      content: h.content
    }));

    const response = await groq.chat.completions.create({
      messages: [
        { role: 'system', content: AGENT_SYSTEM_INSTRUCTIONS[agentType] },
        ...formattedHistory as any[],
        { role: 'user', content: message }
      ],
      model: REQUESTED_MODEL_ID,
    });

    return response.choices[0]?.message?.content || "I'm having trouble thinking right now. Please try again.";
  } catch (error) {
    console.error("Groq API Error:", error);
    return "Sorry, I encountered an error connecting to the AI service.";
  }
};

// Note: Groq does not have a native WebSocket "LiveClient" for audio like Gemini.
// We are removing getLiveClient and implementing a text-based STT fallback in LiveInterview.tsx.

const extractJson = (text: string) => {
    try {
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (jsonMatch) return JSON.parse(jsonMatch[0]);
        return JSON.parse(text);
    } catch (e) {
        console.error("Failed to parse JSON from AI response:", text);
        return {};
    }
};

export const parseResumeWithGroq = async (base64Data: string, mimeType: string) => {
  try {
    let decodedText = '';
    
    if (mimeType.includes('pdf')) {
        try {
            const binaryString = atob(base64Data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            const pdf = await pdfjsLib.getDocument({ data: bytes }).promise;
            let fullText = '';
            
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const textContent = await page.getTextContent();
                const pageText = textContent.items.map((item: any) => item.str).join(' ');
                fullText += pageText + ' \n';
            }
            decodedText = fullText.substring(0, 15000); // Limit length
        } catch (pdfErr) {
            console.error("PDF.js parsing failed", pdfErr);
            decodedText = atob(base64Data).replace(/[^\x20-\x7E\n\r\t]/g, '').substring(0, 15000);
        }
    } else {
        decodedText = atob(base64Data).substring(0, 15000); 
    }

    const prompt = `
      Analyze this resume text and extract the following information in JSON format:
      - currentTitle: The candidate's most recent or current job title.
      - skills: A comma-separated string of technical and soft skills.
      - location: The candidate's current location (City, Country).
      - targetRole: A recommended next role based on their experience.
      
      Respond with ONLY the raw JSON object and nothing else.
      
      Resume Text:
      ${decodedText}
    `;

    const response = await groq.chat.completions.create({
      messages: [
        { role: 'system', content: 'You are an expert resume parser. You output only valid JSON.' },
        { role: 'user', content: prompt }
      ],
      model: REQUESTED_MODEL_ID,
      temperature: 0.1,
    });

    return extractJson(response.choices[0]?.message?.content || "{}");
  } catch (error) {
    console.error("Resume parsing error:", error);
    return null;
  }
};

export const analyzeCandidateResume = async (
    base64Data: string, 
    mimeType: string, 
    criteria: ScannerCriteria
): Promise<Candidate> => {
    try {
        let decodedText = '';
        
        if (mimeType.includes('pdf')) {
            try {
                const binaryString = atob(base64Data);
                const len = binaryString.length;
                const bytes = new Uint8Array(len);
                for (let i = 0; i < len; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                
                const pdf = await pdfjsLib.getDocument({ data: bytes }).promise;
                let fullText = '';
                
                for (let i = 1; i <= pdf.numPages; i++) {
                    const page = await pdf.getPage(i);
                    const textContent = await page.getTextContent();
                    const pageText = textContent.items.map((item: any) => item.str).join(' ');
                    fullText += pageText + ' \n';
                }
                decodedText = fullText.substring(0, 15000);
            } catch (pdfErr) {
                console.error("PDF.js parsing failed", pdfErr);
                decodedText = atob(base64Data).replace(/[^\x20-\x7E\n\r\t]/g, '').substring(0, 15000);
            }
        } else {
            decodedText = atob(base64Data).substring(0, 15000);
        }

        const prompt = `
        You are an AI Recruitment Engine. Analyze the attached resume text against these strict criteria:
        
        CRITERIA:
        1. Target Role: ${criteria.role}
        2. Experience Range: ${criteria.minExp} to ${criteria.maxExp} years.
        3. Custom Requirement: "${criteria.customPrompt}"
        4. Check for Bias: ${criteria.filterBias ? "Yes (Flag generic pronouns, age indicators, marital status)" : "No"}
        5. Check for Duplicates: ${criteria.filterDuplicates ? "Yes (Generate a short hash of the resume text)" : "No"}

        OUTPUT REQUIREMENTS:
        Return a JSON object matching this structure exactly (respond with ONLY the JSON object):
        {
            "name": "Candidate Name",
            "role": "Current Role found in resume",
            "experience": number (total years),
            "matchScore": number (0-100 based on fit),
            "status": "passed" | "failed",
            "flags": ["list", "of", "red", "flags", "or", "bias", "issues"],
            "agentNotes": {
                "screener": "Comment on experience vs requirement (e.g. '5y matches range 2-10y')",
                "biasCheck": "Comment on any bias found or 'Clean'",
                "tech": "Comment on specific skill matches from custom requirement",
                "referee": "Final short verdict"
            }
        }

        Logic for Status:
        - FAIL if experience is outside range (${criteria.minExp}-${criteria.maxExp}).
        - FAIL if matchScore < 60.
        - FAIL if bias detected and filterBias is true.
        - OTHERWISE "passed".
        
        Resume Text (May be garbled if PDF):
        ${decodedText}
        `;

        const response = await groq.chat.completions.create({
            messages: [
                { role: 'system', content: 'You are an expert HR recruitment engine. Output strictly valid JSON without markdown formatting.' },
                { role: 'user', content: prompt }
            ],
            model: REQUESTED_MODEL_ID,
            temperature: 0.1,
        });

        const result = extractJson(response.choices[0]?.message?.content || "{}");
        
        const defaultResult = {
            name: "Unknown Candidate",
            role: "N/A",
            experience: 0,
            matchScore: 0,
            status: "failed",
            flags: ["Could not parse resume"],
            agentNotes: {
                screener: "Failed to parse",
                biasCheck: "N/A",
                tech: "N/A",
                referee: "System Error"
            }
        };

        return {
            id: `cand_${Date.now()}`,
            ...defaultResult,
            ...result,
            agentNotes: { ...defaultResult.agentNotes, ...(result.agentNotes || {}) }
        };

    } catch (error) {
        console.error("Bulk Analysis Error:", error);
        return {
            id: `err_${Date.now()}`,
            name: "Unknown Candidate (Error)",
            role: "N/A",
            experience: 0,
            matchScore: 0,
            status: "failed",
            flags: ["Processing Error"],
            agentNotes: {
                screener: "Failed to parse",
                biasCheck: "N/A",
                tech: "N/A",
                referee: "System Error"
            }
        };
    }
};

export const analyzeCourseWithGroq = async (url: string): Promise<CourseRecommendation> => {
    try {
        const prompt = `Analyze this course URL/Platform string for potential fraud, quality, and ROI for a Senior Software Engineer. 
            URL: ${url}
            
            Return JSON with keys (respond with ONLY the JSON object):
            - title: Inferred course title
            - provider: Inferred provider name
            - duration: Estimated duration
            - cost: Estimated cost number (in INR)
            - roiScore: 0-100
            - matchReason: Why it fits/doesn't fit
            - verified: boolean (true if reputable provider)
            - fraudAlerts: array of strings (red flags if any)`;
            
        const response = await groq.chat.completions.create({
            messages: [
                { role: 'system', content: 'You are an expert course evaluator. Output strictly valid JSON without markdown formatting.' },
                { role: 'user', content: prompt }
            ],
            model: REQUESTED_MODEL_ID,
            temperature: 0.1,
        });
        
        const data = extractJson(response.choices[0]?.message?.content || "{}");
        return {
            id: `gen_${Date.now()}`,
            title: data.title || "Unknown Course",
            provider: data.provider || "Unknown Provider",
            duration: data.duration || "N/A",
            cost: data.cost || 0,
            roiScore: data.roiScore || 50,
            matchReason: data.matchReason || "Analysis complete",
            verified: data.verified || false,
            fraudAlerts: data.fraudAlerts
        };
    } catch (e) {
        console.error("Course Analysis Error", e);
        return {
            id: 'err',
            title: 'Analysis Failed',
            provider: 'System',
            duration: '-',
            cost: 0,
            roiScore: 0,
            matchReason: "Could not analyze this URL.",
            verified: false
        };
    }
}
