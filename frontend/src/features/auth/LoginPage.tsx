import { Link } from "react-router-dom";
import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError } from "@/api/client";
import { useAuthConfig, useLogin, useRegistro } from "@/api/queries";
import { usePreferencias } from "@/hooks/usePreferencias";
import type { MsgKey } from "@/i18n/messages";
import nebula from "@/styles/nebula.module.css";
import css from "./Login.module.css";
import { LogoMontor } from "@/components/LogoMontor";

type Tab = "login" | "register";

const CODIGOS_CONOCIDOS: MsgKey[] = [
  "invalid_credentials",
  "missing_fields",
  "username_taken",
  "weak_password",
  "too_many_attempts",
  "google",
  "google_email",
  "google_state",
  "google_no_configurado",
];

function esCodigoConocido(codigo: string): codigo is MsgKey {
  return (CODIGOS_CONOCIDOS as string[]).includes(codigo);
}

export function LoginPage() {
  const { modo, lang, toggleModo, toggleLang, t } = usePreferencias();
  const login = useLogin();
  const registro = useRegistro();
  const authConfig = useAuthConfig();

  const [tab, setTab] = useState<Tab>("login");
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [registerForm, setRegisterForm] = useState({ username: "", password: "" });
  // Se guarda el código, no el texto ya traducido, para que si cambiás el
  // idioma mientras el error está en pantalla se retraduzca solo en vez de
  // quedar congelado en el idioma de cuando ocurrió.
  const [error, setError] = useState<string | null>(() => {
    // La vuelta de Google no pasa por fetch: informa por la query string.
    if (typeof window === "undefined") return null;
    return new URLSearchParams(window.location.search).get("error");
  });
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

      <div className={css.split}>
        {/* Panel de marca: solo aparece en pantallas anchas. En un monitor
            grande la tarjeta sola quedaba perdida en el vacío, y este espacio
            es además el último lugar donde se puede explicar qué es Montor
            antes de que la persona decida entrar. */}
        <div className={css.marca}>
          <div className={css.marcaLogo}>
            <LogoMontor />
            <span>{t("montor")}</span>
          </div>
          <h2 className={css.marcaTitulo}>{t("login_titular")}</h2>
          <p className={css.marcaBajada}>{t("login_bajada")}</p>
          <ul className={css.marcaPuntos}>
            <li>
              <span aria-hidden="true">💵</span>
              <div>
                <strong>{t("login_punto_monedas")}</strong>
                <em>{t("login_punto_monedas_d")}</em>
              </div>
            </li>
            <li>
              <span aria-hidden="true">✈️</span>
              <div>
                <strong>{t("login_punto_viajes")}</strong>
                <em>{t("login_punto_viajes_d")}</em>
              </div>
            </li>
            <li>
              <span aria-hidden="true">🤖</span>
              <div>
                <strong>{t("login_punto_ia")}</strong>
                <em>{t("login_punto_ia_d")}</em>
              </div>
            </li>
          </ul>
        </div>

      <div className={css.card}>
        <div className={css.logo}>
          <LogoMontor />
        </div>
        <h1 className={css.h1}>{t("montor")}</h1>
        <p className={css.subtitle}>{t("administra_ingresos_gastos")}</p>

        {authConfig.data?.google && (
          <>
            {/* Link y no fetch: el OAuth necesita una navegación de verdad
                del navegador hacia Google, no una llamada en segundo plano. */}
            <a className={css.google} href="/api/montor/auth/google">
              <svg viewBox="0 0 48 48" aria-hidden="true">
                <path fill="#4285F4" d="M45.1 24.5c0-1.6-.1-2.7-.4-4H24v7.3h12.1c-.2 1.9-1.6 4.9-4.5 6.8l-.1.3 6.6 5.1.5.1c4.2-3.9 6.5-9.6 6.5-15.6z"/>
                <path fill="#34A853" d="M24 46c5.9 0 10.9-2 14.5-5.3l-6.9-5.4c-1.9 1.3-4.4 2.2-7.6 2.2-5.8 0-10.7-3.8-12.5-9.1l-.3.1-6.8 5.3-.1.3C7.9 41 15.4 46 24 46z"/>
                <path fill="#FBBC05" d="M11.5 28.4c-.5-1.4-.7-2.9-.7-4.4s.3-3 .7-4.4v-.3l-6.9-5.4-.2.1C2.8 17 2 20.4 2 24s.8 7 2.4 10l7.1-5.6z"/>
                <path fill="#EB4335" d="M24 9.5c4.1 0 6.9 1.8 8.5 3.3l6.2-6C34.9 3.4 29.9 1 24 1 15.4 1 7.9 6 4.4 14l7.1 5.6c1.8-5.3 6.7-9.1 12.5-9.1z"/>
              </svg>
              {t("continuar_con_google")}
            </a>
            <div className={css.separador}><span>{t("o")}</span></div>
          </>
        )}

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
    </div>
  );
}
