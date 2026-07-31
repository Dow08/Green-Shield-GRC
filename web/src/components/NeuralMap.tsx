import { motion } from "framer-motion";
import { Network, Database, Shield, FileText, BrainCircuit, Activity } from "lucide-react";
import { useEffect, useState } from "react";

const NODES = [
  { id: "core", x: 50, y: 50, icon: BrainCircuit, label: "IA GRC", desc: "Moteur d'Intelligence Artificielle central", color: "text-[var(--g1)]", size: 36 },
  { id: "iso27001", x: 20, y: 30, icon: Shield, label: "ISO 27001", desc: "Référentiel de sécurité de l'information", color: "text-[var(--sky)]", size: 24 },
  { id: "ebios", x: 80, y: 30, icon: Activity, label: "EBIOS RM", desc: "Méthode d'analyse des risques", color: "text-[var(--rose)]", size: 24 },
  { id: "tprm", x: 20, y: 70, icon: Network, label: "TPRM", desc: "Gestion des risques tiers (Fournisseurs)", color: "text-[var(--amber,#ffcf6b)]", size: 24 },
  { id: "assets", x: 80, y: 70, icon: Database, label: "Actifs", desc: "Patrimoine de données et infrastructures", color: "text-blue-400", size: 24 },
  { id: "audit", x: 50, y: 15, icon: FileText, label: "Auditcraft", desc: "Génération automatisée de rapports", color: "text-purple-400", size: 24 },
];

const EDGES = [
  { from: "core", to: "iso27001" },
  { from: "core", to: "ebios" },
  { from: "core", to: "tprm" },
  { from: "core", to: "assets" },
  { from: "core", to: "audit" },
  { from: "iso27001", to: "tprm" },
  { from: "ebios", to: "assets" },
  { from: "iso27001", to: "audit" },
];

export function NeuralMap() {
  const [activeEdge, setActiveEdge] = useState<number | null>(null);

  // Animation aléatoire des flux
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveEdge(Math.floor(Math.random() * EDGES.length));
      setTimeout(() => setActiveEdge(null), 1500);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-full h-[350px] glass-2 rounded-2xl p-4 overflow-hidden flex flex-col">
      <h3 className="text-sm font-bold flex items-center gap-2 text-[var(--soft)] z-10">
        <Network size={16} className="text-[var(--g1)]" /> Carte Neurale des Référentiels
      </h3>
      
      <div className="flex-1 relative w-full h-full">
        {/* Lignes de connexion (SVG) */}
        <svg className="absolute inset-0 w-full h-full" style={{ pointerEvents: "none" }}>
          <defs>
            <linearGradient id="edge-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="rgba(46,230,160,0.1)" />
              <stop offset="100%" stopColor="rgba(46,230,160,0.6)" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          
          {EDGES.map((edge, i) => {
            const fromNode = NODES.find(n => n.id === edge.from)!;
            const toNode = NODES.find(n => n.id === edge.to)!;
            const isActive = activeEdge === i;
            
            return (
              <motion.line
                key={i}
                x1={`${fromNode.x}%`}
                y1={`${fromNode.y}%`}
                x2={`${toNode.x}%`}
                y2={`${toNode.y}%`}
                stroke={isActive ? "url(#edge-gradient)" : "rgba(255,255,255,0.05)"}
                strokeWidth={isActive ? 2 : 1}
                filter={isActive ? "url(#glow)" : ""}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1, delay: i * 0.1 }}
              />
            );
          })}
        </svg>

        {/* Nœuds */}
        {NODES.map((node, i) => {
          const Icon = node.icon;
          return (
            <motion.div
              key={node.id}
              className="absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-2 group cursor-crosshair z-10"
              style={{ left: `${node.x}%`, top: `${node.y}%` }}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", delay: 0.5 + i * 0.1 }}
              whileHover={{ scale: 1.15 }}
            >
              <div className={`grid place-items-center rounded-full bg-black/40 border border-white/10 shadow-[0_0_20px_rgba(0,0,0,0.5)] transition group-hover:border-[var(--g1)] group-hover:shadow-[0_0_20px_rgba(46,230,160,0.2)]`} style={{ width: node.size + 24, height: node.size + 24 }}>
                <Icon size={node.size} className={`${node.color} opacity-80 group-hover:opacity-100 transition`} />
              </div>
              <div className="text-[10px] font-bold text-[var(--soft)] group-hover:text-white transition bg-black/60 px-2 py-0.5 rounded-full border border-white/5 whitespace-nowrap">
                {node.label}
              </div>
              
              {/* Tooltip au survol */}
              <div className="absolute top-full mt-2 w-max max-w-[150px] bg-black/90 text-white text-[10px] p-2 rounded-lg border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 text-center shadow-xl">
                {node.desc}
              </div>
            </motion.div>
          );
        })}

        {/* Pulsations actives */}
        {activeEdge !== null && (
          <motion.div
            className="absolute w-3 h-3 bg-[var(--g1)] rounded-full blur-[2px]"
            initial={{ 
              left: `${NODES.find(n => n.id === EDGES[activeEdge].from)!.x}%`, 
              top: `${NODES.find(n => n.id === EDGES[activeEdge].from)!.y}%`,
              opacity: 1
            }}
            animate={{ 
              left: `${NODES.find(n => n.id === EDGES[activeEdge].to)!.x}%`, 
              top: `${NODES.find(n => n.id === EDGES[activeEdge].to)!.y}%`,
              opacity: 0
            }}
            transition={{ duration: 1.5, ease: "easeInOut" }}
          />
        )}
      </div>
    </div>
  );
}
