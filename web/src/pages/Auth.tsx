import React, { useState } from "react";
import { api } from "../lib/api";
import { Lock, Mail, Key } from "lucide-react";

export function Auth({ view, setView, onLogin }: { view: "login" | "register", setView: (v: "login" | "register") => void, onLogin: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    
    try {
      if (view === "login") {
        const res = await api.auth.login({ email, password });
        localStorage.setItem("greenshield_token", res.access_token);
        localStorage.setItem("greenshield_premium", res.is_premium ? "1" : "0");
        onLogin();
      } else {
        await api.auth.register({ email, password });
        setView("login");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Une erreur est survenue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl border border-[var(--stroke)] bg-white/[0.02] p-8 shadow-2xl backdrop-blur-xl">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500">
            {view === "login" ? <Lock size={32} /> : <Key size={32} />}
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            {view === "login" ? "Connexion" : "Créer un compte"}
          </h1>
          <p className="mt-2 text-sm text-[var(--soft)]">
            {view === "login" ? "Accédez à votre espace GREEN SHIELD" : "Rejoignez la plateforme d'audit IA"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Adresse email"
                className="w-full rounded-xl border border-[var(--stroke)] bg-black/20 py-3 pl-10 pr-4 text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>
          <div>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mot de passe"
                className="w-full rounded-xl border border-[var(--stroke)] bg-black/20 py-3 pl-10 pr-4 text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-600 py-3 font-semibold text-white transition-all hover:bg-emerald-500 hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] disabled:opacity-50"
          >
            {loading ? "Chargement..." : view === "login" ? "Se connecter" : "S'inscrire"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-[var(--soft)]">
          {view === "login" ? (
            <p>
              Pas encore de compte ?{" "}
              <button onClick={() => setView("register")} className="text-emerald-500 hover:underline">
                Créer un compte
              </button>
            </p>
          ) : (
            <p>
              Déjà inscrit ?{" "}
              <button onClick={() => setView("login")} className="text-emerald-500 hover:underline">
                Se connecter
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
