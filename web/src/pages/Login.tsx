import React, { useState } from "react";
import { Lock } from "lucide-react";
import { api } from "../lib/api";

interface LoginProps {
  onSuccess: () => void;
}

export function Login({ onSuccess }: LoginProps) {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) return;
    
    setLoading(true);
    setError("");
    
    // We store the token temporarily in memory/sessionStorage to test it
    sessionStorage.setItem("greenshield_token", token.trim());
    
    try {
      // Ping an authenticated route to verify the token
      await api.modules(); 
      onSuccess();
    } catch (err: any) {
      sessionStorage.removeItem("greenshield_token");
      setError("Jeton d'accès incorrect ou refusé.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--fg)] flex items-center justify-center p-4">
      <div className="tile p-8 max-w-md w-full space-y-6">
        <div className="flex flex-col items-center space-y-2">
          <div className="w-12 h-12 rounded-full bg-[var(--accent)]/10 flex items-center justify-center mb-2">
            <Lock className="w-6 h-6 text-[var(--accent)]" />
          </div>
          <h1 className="text-xl font-medium tracking-tight">Authentification API</h1>
          <p className="text-sm text-[var(--soft)] text-center">
            GREEN SHIELD est verrouillé. Entrez le jeton d'accès pour continuer.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--soft)] mb-1">
              Jeton d'accès (Bearer Token)
            </label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="w-full px-3 py-2 bg-[var(--bg2)] border border-[var(--stroke)] rounded text-[var(--fg)] focus:outline-none focus:border-[var(--accent)] transition-colors"
              placeholder="Ex: a1b2c3d4..."
              autoFocus
            />
          </div>
          
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={!token.trim() || loading}
            className="w-full py-2 bg-[var(--accent)] text-white rounded font-medium hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? "Vérification..." : "Déverrouiller le cockpit"}
          </button>
        </form>
      </div>
    </div>
  );
}
