import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import type { Lang, MsgKey } from "@/i18n/messages";
import { tr as traducir } from "@/i18n/messages";

type Modo = "dark" | "light";

type Preferencias = {
  modo: Modo;
  lang: Lang;
  toggleModo: () => void;
  toggleLang: () => void;
  /** Traduce una clave al idioma activo. */
  t: (key: MsgKey) => string;
};

const Ctx = createContext<Preferencias | null>(null);

// Mismas claves de localStorage que usan las páginas Jinja, así el tema y el
// idioma se mantienen al navegar entre una página migrada y una que no.
const KEY_MODO = "modo";
const KEY_LANG = "lang";

function leer<T extends string>(key: string, valores: readonly T[], fallback: T): T {
  try {
    const v = localStorage.getItem(key);
    return valores.includes(v as T) ? (v as T) : fallback;
  } catch {
    return fallback;
  }
}

export function PreferenciasProvider({ children }: { children: ReactNode }) {
  const [modo, setModo] = useState<Modo>(() => leer(KEY_MODO, ["dark", "light"] as const, "dark"));
  const [lang, setLang] = useState<Lang>(() => leer(KEY_LANG, ["es", "en"] as const, "es"));

  useEffect(() => {
    document.body.classList.toggle("light", modo === "light");
    try {
      localStorage.setItem(KEY_MODO, modo);
    } catch {
      /* modo incógnito: la preferencia simplemente no persiste */
    }
  }, [modo]);

  useEffect(() => {
    document.documentElement.lang = lang;
    try {
      localStorage.setItem(KEY_LANG, lang);
    } catch {
      /* idem */
    }
  }, [lang]);

  const toggleModo = useCallback(() => setModo((m) => (m === "light" ? "dark" : "light")), []);
  const toggleLang = useCallback(() => setLang((l) => (l === "en" ? "es" : "en")), []);
  const t = useCallback((key: MsgKey) => traducir(key, lang), [lang]);

  const value = useMemo(
    () => ({ modo, lang, toggleModo, toggleLang, t }),
    [modo, lang, toggleModo, toggleLang, t],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function usePreferencias(): Preferencias {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("usePreferencias necesita estar dentro de <PreferenciasProvider>");
  return ctx;
}
