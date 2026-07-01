import React from 'react';
import { motion } from 'framer-motion';
import { Briefcase, TrendingUp, Target, Award, Search, Globe, Zap, Laptop, FileText, Coffee } from 'lucide-react';

// --- Mouse Spotlight ---
export const MouseSpotlight = () => {
    const [mousePosition, setMousePosition] = React.useState({ x: 0, y: 0 });

    React.useEffect(() => {
        const updateMousePosition = (ev: MouseEvent) => {
            setMousePosition({ x: ev.clientX, y: ev.clientY });
        };
        window.addEventListener('mousemove', updateMousePosition);
        return () => window.removeEventListener('mousemove', updateMousePosition);
    }, []);

    return (
        <div
            className="pointer-events-none fixed inset-0 z-30 transition-opacity duration-300"
            style={{
                background: `radial-gradient(600px circle at ${mousePosition.x}px ${mousePosition.y}px, rgba(37, 99, 235, 0.05), transparent 80%)`
            }}
        />
    );
};

// --- Animated Background (Subtle Dashboard Theme) ---
export const AuroraBackground = () => (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden bg-[#F8FAFC]">
        {/* Subtle Grid Pattern Overlay */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSA0MCAwIEwgMCAwIDAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgwLCAwLCAwLCAwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-40 mix-blend-multiply" />
        
        {/* Ambient Glowing Orbs - Very Soft */}
        <motion.div 
            animate={{ 
                x: [-20, 20, -20], 
                y: [-10, 10, -10],
                opacity: [0.03, 0.06, 0.03],
            }}
            transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
            className="absolute top-[-20%] left-[-10%] w-[60vw] h-[60vw] max-w-[800px] max-h-[800px] rounded-full bg-blue-600 blur-[120px]"
        />
        <motion.div 
            animate={{ 
                x: [20, -20, 20], 
                y: [10, -10, 10],
                opacity: [0.02, 0.05, 0.02],
            }}
            transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
            className="absolute bottom-[-20%] right-[-10%] w-[70vw] h-[70vw] max-w-[1000px] max-h-[1000px] rounded-full bg-indigo-500 blur-[120px]"
        />

        {/* Soft Vignette Mask */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#F8FAFC]/50 to-[#F8FAFC]" />
    </div>
);

// --- Premium Glass Card ---
interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
    children?: React.ReactNode;
    className?: string;
    hoverEffect?: boolean;
    onClick?: React.MouseEventHandler<HTMLDivElement>;
}

export const GlassCard: React.FC<GlassCardProps> = ({ children, className = "", hoverEffect = true, onClick, ...props }) => (
    <motion.div 
        whileHover={hoverEffect ? { y: -2, boxShadow: "0 15px 30px rgba(37, 99, 235, 0.1)" } : {}}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className={`glass-panel-premium rounded-[2rem] relative z-10 bg-white/70 backdrop-blur-[20px] border border-slate-200/60 shadow-lg ${className}`}
        onClick={onClick}
        {...(props as any)}
    >
        {children}
    </motion.div>
);

// --- Neon Button (Now "Blue Button") ---
interface NeonButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'danger';
    icon?: React.ReactNode;
    children?: React.ReactNode;
    className?: string;
    onClick?: React.MouseEventHandler<HTMLButtonElement>;
    disabled?: boolean;
}

export const NeonButton = ({ children, variant = 'primary', icon, className = "", onClick, disabled, ...props }: NeonButtonProps) => {
    // Primary: Blue background, White text
    // Secondary: White background, Blue text
    const variants = {
        primary: "bg-primary text-white border border-transparent shadow-neon hover:bg-blue-700 hover:shadow-neon-strong hover:-translate-y-0.5",
        secondary: "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-primary/30 hover:text-primary hover:shadow-md hover:-translate-y-0.5",
        danger: "bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 hover:shadow-md"
    };

    const baseStyles = "relative px-6 py-3 rounded-xl font-display font-bold text-sm tracking-wide transition-all duration-300 flex items-center justify-center gap-2 overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:hover:translate-y-0";

    return (
        <button className={`${baseStyles} ${variants[variant]} ${className}`} onClick={onClick} disabled={disabled} {...props}>
            <span className="relative z-10 flex items-center gap-2">{icon}{children}</span>
        </button>
    );
};

// --- Floating Orb (Static) ---
export const FloatingOrb = ({ color = "bg-primary", size = "w-32 h-32", className = "" }) => (
    <div
        className={`${size} rounded-full ${color} blur-[80px] opacity-20 absolute pointer-events-none mix-blend-multiply ${className}`}
    />
);

// --- Gradient Text ---
export const GradientText = ({ children, className = "" }: { children: React.ReactNode, className?: string }) => (
    <span className={`bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 ${className}`}>
        {children}
    </span>
);