import { useState } from "react";
import { motion } from "framer-motion";
import { Cloud, Lock, Server, Link2, Search, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { api } from "../lib/api";
import type { ProjectState } from "../types";

interface Props {
  project: ProjectState;
  onChange: (project: ProjectState) => void;
}

export function ConnectorsPanel({ project, onChange }: Props) {
  const [scanning, setScanning] = useState<string | null>(null);
  const [result, setResult] = useState<{ [key: string]: { status: string; count: number; details: string } }>({});

  const handleScan = async (connectorId: string) => {
    setScanning(connectorId);
    try {
      const res = await api.projects.scanConnector(project.id, connectorId);
      setResult(prev => ({ ...prev, [connectorId]: { status: res.status, count: res.updates_count, details: res.details } }));
      
      // On recharge le projet pour rafraichir le Kanban (si un scan met à jour un statut)
      const updatedProject = await api.projects.get(project.id);
      onChange(updatedProject);
    } catch (e) {
      console.error(e);
      alert("Erreur lors de la communication avec le connecteur.");
    } finally {
      setScanning(null);
    }
  };

  const connectors = [
    {
      id: "microsoft_365",
      name: "Microsoft 365 / Entra ID",
      icon: Cloud,
      description: "Vérifie les configurations d'accès (MFA, Conditional Access) sur votre tenant.",
      color: "text-blue-500",
      bg: "bg-blue-500/10",
      border: "border-blue-500/30"
    },
    {
      id: "aws",
      name: "Amazon Web Services",
      icon: Server,
      description: "Analyse le chiffrement (KMS, S3) et la gestion des identités IAM.",
      color: "text-[#FF9900]",
      bg: "bg-[#FF9900]/10",
      border: "border-[#FF9900]/30"
    },
    {
      id: "github",
      name: "GitHub Enterprise",
      icon: Lock,
      description: "Audite la sécurité du code source, les secrets et les revues de code.",
      color: "text-white",
      bg: "bg-white/10",
      border: "border-white/30"
    }
  ];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h3 className="text-xl font-bold flex items-center gap-2">
          <Link2 className="text-[var(--accent)]" /> Continuous Compliance
        </h3>
        <p className="text-sm text-[var(--soft)]">
          Connectez l'infrastructure de votre client pour collecter des preuves automatisées et valider instantanément les exigences ISO 27001.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {connectors.map((c) => {
          const Icon = c.icon;
          const isScanning = scanning === c.id;
          const scanResult = result[c.id];

          return (
            <div key={c.id} className={`glass p-5 border flex flex-col justify-between ${scanResult ? 'border-[var(--accent)]' : 'border-white/10'}`}>
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className={`p-3 rounded-lg ${c.bg} ${c.color}`}>
                    <Icon size={24} />
                  </div>
                  {scanResult && (
                    <div className="text-[var(--accent)] flex items-center gap-1 text-xs font-bold bg-[var(--accent)]/10 px-2 py-1 rounded">
                      <CheckCircle2 size={12} /> Sync
                    </div>
                  )}
                </div>
                <h4 className="font-bold text-[var(--ink)] mb-1">{c.name}</h4>
                <p className="text-xs text-[var(--faint)] leading-relaxed h-10">{c.description}</p>
              </div>

              <div className="mt-5 pt-4 border-t border-white/5">
                {scanResult ? (
                  <div className="flex flex-col gap-2">
                    <div className="text-xs text-[var(--soft)] flex items-center gap-2">
                      <AlertCircle size={14} className="text-[var(--sky)]" />
                      {scanResult.count} exigence(s) validée(s)
                    </div>
                    <div className="text-[10px] text-[var(--faint)] italic truncate">
                      {scanResult.details}
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => handleScan(c.id)}
                    disabled={isScanning || scanning !== null}
                    className="w-full py-2 rounded-lg bg-white/5 hover:bg-white/10 text-sm font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isScanning ? (
                      <>
                        <Loader2 size={16} className="animate-spin" /> Analyse...
                      </>
                    ) : (
                      <>
                        <Search size={16} /> Lancer le scan
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
