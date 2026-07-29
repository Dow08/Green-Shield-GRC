import type { ComponentType } from "react";
import { Shield, FolderKanban, Bot, Radar } from "lucide-react";

const ICONS: Record<string, ComponentType<{ size?: number; strokeWidth?: number }>> = {
  shield: Shield,
  missions: FolderKanban,
  copilot: Bot,
  collect: Radar,
};

export function iconFor(name: string): ComponentType<{ size?: number; strokeWidth?: number }> {
  return ICONS[name] ?? Shield;
}
