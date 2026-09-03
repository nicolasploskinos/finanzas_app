import { Link } from "react-router-dom";
import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError } from "@/api/client";
import { useLogin, useRegistro } from "@/api/queries";
import { usePreferencias } from "@/hooks/usePreferencias";
import type { MsgKey } from "@/i18n/messages";
import nebula from "@/styles/nebula.module.css";
import css from "./Login.module.css";

type Tab = "login" | "register";

const CODIGOS_CONOCIDOS: MsgKey[] = [
  "invalid_credentials",
  "missing_fields",
  "username_taken",
  "weak_password",
  "too_many_attempts",
];

function esCodigoConocido(codigo: string): codigo is MsgKey {
  return (CODIGOS_CONOCIDOS as string[]).includes(codigo);
}

export function LoginPage() {
  const { modo, lang, toggleModo, toggleLang, t } = usePreferencias();
  const login = useLogin();
  const registro = useRegistro();

  const [tab, setTab] = useState<Tab>("login");
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [registerForm, setRegisterForm] = useState({ username: "", password: "" });
  // Se guarda el código, no el texto ya traducido, para que si cambiás el
  // idioma mientras el error está en pantalla se retraduzca solo en vez de
  // quedar congelado en el idioma de cuando ocurrió.
  const [error, setError] = useState<string | null>(null);
  // Se incrementa en cada error nuevo y se usa como `key` del cartel: eso
  // fuerza a React a remontar el nodo, así el shake se repite en intentos
  // fallidos consecutivos en vez de quedarse quieto la segunda vez.
  const [errorTick, setErrorTick] = useState(0);

  function mostrarError(codigo: string) {
    setError(codigo);
    setErrorTick((n) => n + 1);
  }

  function cambiarTab(t: Tab) {
    setTab(t);
    setError(null);
  }

  async function alEnviarLogin(e: FormEvent) {
    e.preventDefault();
    const username = loginForm.username.trim();
    if (!username || !loginForm.password) {
      mostrarError("missing_fields");
      return;
    }
    try {
      await login.mutateAsync({ username, password: loginForm.password });
      window.location.href = "/montor";
    } catch (err) {
      mostrarError(err instanceof ApiError ? err.message : "invalid_credentials");
    }
  }

  async function alEnviarRegistro(e: FormEvent) {
    e.preventDefault();
    const username = registerForm.username.trim();
    if (!username || !registerForm.password) {
      mostrarError("missing_fields");
      return;
    }
    try {
      await registro.mutateAsync({ username, password: registerForm.password });
      window.location.href = "/montor";
    } catch (err) {
      mostrarError(err instanceof ApiError ? err.message : "missing_fields");
    }
  }

  return (
    <div className={nebula.theme} data-tema="nebula">
    <div className={css.bg}>
      <div className={css.topActions}>
        <button
          className={css.langBtn}
          onClick={toggleLang}
          title="Switch language"
          aria-label="Switch language"
        >
          {lang === "en" ? "ES" : "EN"}
        </button>
        <button
          className={css.modoBtn}
          onClick={toggleModo}
          title="Cambiar modo"
          aria-label="Cambiar modo claro/oscuro"
        >
          {modo === "light" ? "☀️" : "🌙"}
        </button>
      </div>

      <div className={css.card}>
        <div className={css.logo}>
          <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="44" fill="none" stroke="currentColor" strokeWidth="7" />
            <rect x="28" y="48" width="9" height="22" rx="3" fill="currentColor" />
            <rect x="45" y="38" width="9" height="32" rx="3" fill="currentColor" />
            <rect x="62" y="28" width="9" height="42" rx="3" fill="currentColor" />
          </svg>
        </div>
        <h1 className={css.h1}>{t("montor")}</h1>
        <p className={css.subtitle}>{t("administra_ingresos_gastos")}</p>

        <div className={css.tabs}>
          <button
            className={`${css.tab} ${tab === "login" ? css.active : ""}`}
            onClick={() => cambiarTab("login")}
          >
            {t("ingresar")}
          </button>
          <button
            className={`${css.tab} ${tab === "register" ? css.active : ""}`}
            onClick={() => cambiarTab("register")}
          >
            {t("registrarse")}
          </button>
        </div>

        {error && (
          <div key={errorTick} className={`${css.error} ${css.shake}`} role="alert">
            {esCodigoConocido(error) ? t(error) : error}
          </div>
        )}

        {tab === "login" ? (
          <form key="login" className={css.fadeIn} onSubmit={alEnviarLogin}>
            <div className={css.campo}>
              <label htmlFor="l-user">{t("usuario")}</label>
              <input
                id="l-user"
                type="text"
                placeholder="ej: nico123"
                autoComplete="username"
                value={loginForm.username}
                onChange={(e) => setLoginForm((f) => ({ ...f, username: e.target.value }))}
              />
            </div>
            <div className={css.campo}>
              <label htmlFor="l-pass">{t("contrasena")}</label>
              <input
                id="l-pass"
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                value={loginForm.password}
                onChange={(e) => setLoginForm((f) => ({ ...f, password: e.target.value }))}
              />
            </div>
            <button className={css.btn} type="submit" disabled={login.isPending}>
              {t("ingresar")}
            </button>
          </form>
        ) : (
          <form key="register" className={css.fadeIn} onSubmit={alEnviarRegistro}>
            <div className={css.campo}>
              <label htmlFor="r-user">{t("usuario")}</label>
              <input
                id="r-user"
                type="text"
                placeholder="ej: nico123"
                autoComplete="username"
                value={registerForm.username}
                onChange={(e) => setRegisterForm((f) => ({ ...f, username: e.target.value }))}
              />
            </div>
            <div className={css.campo}>
              <label htmlFor="r-pass">{t("contrasena")}</label>
              <input
                id="r-pass"
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                value={registerForm.password}
                onChange={(e) => setRegisterForm((f) => ({ ...f, password: e.target.value }))}
              />
            </div>
            <button className={css.btn} type="submit" disabled={registro.isPending}>
              {t("crear_cuenta")}
            </button>
            <p className={css.legal}>
              {lang === "en" ? "By creating an account you agree to our " : "Al crear una cuenta aceptás nuestros "}
              <Link to="/terminos">{t("terminos")}</Link>
              {lang === "en" ? " and " : " y "}
              <Link to="/privacidad">{t("politica_privacidad")}</Link>
            </p>
          </form>
        )}
      </div>
    </div>
    </div>
  );
}
