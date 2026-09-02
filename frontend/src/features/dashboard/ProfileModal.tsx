import { useEffect, useState } from "react";

import { ApiError } from "@/api/client";
import { useCambiarNombre, useCambiarPassword, useCancelarSuscripcion, useCuenta } from "@/api/queries";
import { Modal } from "@/components/Modal";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import { tr } from "@/i18n/messages";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

type Props = {
  abierto: boolean;
  onCerrar: () => void;
  onVerPlanes: () => void;
};

function formatFechaHora(iso: string, lang: "es" | "en"): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(lang === "en" ? "en-US" : "es-AR", { day: "2-digit", month: "long", year: "numeric" });
}

export function ProfileModal({ abierto, onCerrar, onVerPlanes }: Props) {
  const { lang } = usePreferencias();
  const toast = useToast();
  const cuenta = useCuenta(abierto);
  const cambiarNombre = useCambiarNombre();
  const cambiarPassword = useCambiarPassword();
  const cancelarSuscripcion = useCancelarSuscripcion();

  const [nombre, setNombre] = useState("");
  const [actual, setActual] = useState("");
  const [nueva, setNueva] = useState("");

  useEffect(() => {
    if (cuenta.data) setNombre(cuenta.data.username);
  }, [cuenta.data]);

  useEffect(() => {
    if (!abierto) {
      setActual("");
      setNueva("");
    }
  }, [abierto]);

  function errorTexto(err: unknown, fallback: string): string {
    if (err instanceof ApiError && err.message) {
      const traducciones: Record<string, string> = {
        too_short: trd("too_short", lang),
        username_taken: tr("username_taken", lang),
        weak_password: tr("weak_password", lang),
        wrong_password: trd("wrong_password", lang),
      };
      if (traducciones[err.message]) return traducciones[err.message];
    }
    return fallback;
  }

  async function alGuardarNombre() {
    if (nombre.trim().length < 3 || nombre.trim() === cuenta.data?.username) return;
    try {
      await cambiarNombre.mutateAsync(nombre.trim());
      toast(trd("nombre_actualizado", lang));
    } catch (err) {
      toast(errorTexto(err, trd("error_guardar", lang)));
    }
  }

  async function alGuardarPassword() {
    if (nueva.length < 8) {
      toast(tr("weak_password", lang));
      return;
    }
    try {
      await cambiarPassword.mutateAsync({ actual, nueva });
      toast(trd("contrasena_actualizada", lang));
      setActual("");
      setNueva("");
    } catch (err) {
      toast(errorTexto(err, trd("error_guardar", lang)));
    }
  }

  async function alCancelarSuscripcion() {
    if (!confirm(trd("confirm_cancelar_suscripcion", lang))) return;
    try {
      await cancelarSuscripcion.mutateAsync();
      toast(trd("suscripcion_cancelada", lang));
    } catch {
      toast(trd("error_guardar", lang));
    }
  }

  function alCambiarMetodoPago() {
    const ciclo = cuenta.data?.suscripcion?.ciclo ?? "mensual";
    window.location.href = `/api/montor/suscribir?ciclo=${ciclo}`;
  }

  const c = cuenta.data;

  return (
    <Modal abierto={abierto} titulo={trd("perfil", lang)} onCerrar={onCerrar} grande>
      {cuenta.isPending && <div className={css.estado}>{tr("cargando", lang)}</div>}

      {c && (
        <>
          <div className={css.campo}>
            <label htmlFor="perfil-nombre">{trd("nombre_de_usuario", lang)}</label>
            <input
              id="perfil-nombre"
              type="text"
              autoComplete="username"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
          </div>
          <button
            className={css.btnGuardar}
            onClick={alGuardarNombre}
            disabled={cambiarNombre.isPending || nombre.trim().length < 3 || nombre.trim() === c.username}
          >
            {trd("guardar_nombre", lang)}
          </button>

          <div className={css.perfilDivider} />

          <div className={css.perfilSectionTitle}>{trd("cambiar_contrasena", lang)}</div>
          <div className={css.campo}>
            <label htmlFor="perfil-actual">{trd("contrasena_actual", lang)}</label>
            <input
              id="perfil-actual"
              type="password"
              autoComplete="current-password"
              value={actual}
              onChange={(e) => setActual(e.target.value)}
            />
          </div>
          <div className={css.campo}>
            <label htmlFor="perfil-nueva">{trd("contrasena_nueva", lang)}</label>
            <input
              id="perfil-nueva"
              type="password"
              autoComplete="new-password"
              value={nueva}
              onChange={(e) => setNueva(e.target.value)}
            />
          </div>
          <button
            className={css.btnGuardar}
            onClick={alGuardarPassword}
            disabled={cambiarPassword.isPending || !actual || nueva.length < 8}
          >
            {trd("guardar_contrasena", lang)}
          </button>

          <div className={css.perfilDivider} />

          <div className={css.perfilSectionTitle}>{trd("tu_plan", lang)}</div>
          <div className={css.perfilPlanCard}>
            <div className={css.perfilPlanEstado}>
              {c.is_trial
                ? trd("plan_prueba_perfil", lang)
                : c.is_pro
                  ? trd("plan_pro_activo", lang)
                  : trd("plan_gratis_perfil", lang)}
            </div>

            {c.is_pro && !c.is_trial && (
              <>
                <div className={css.perfilPlanFila}>
                  <span>{trd("proximo_pago", lang)}</span>
                  <span>
                    {c.suscripcion?.proximo_pago
                      ? formatFechaHora(c.suscripcion.proximo_pago, lang)
                      : trd("sin_fecha_proximo_pago", lang)}
                  </span>
                </div>
                {c.suscripcion?.ciclo && (
                  <div className={css.perfilPlanFila}>
                    <span>{lang === "en" ? "Billing cycle" : "Ciclo"}</span>
                    <span>{trd(c.suscripcion.ciclo === "anual" ? "ciclo_anual" : "ciclo_mensual", lang)}</span>
                  </div>
                )}

                <button className={css.perfilLinkBtn} onClick={alCambiarMetodoPago}>
                  {trd("cambiar_metodo_pago", lang)}
                </button>
                <p className={css.perfilAyuda}>{trd("cambiar_metodo_pago_detalle", lang)}</p>

                <button
                  className={`${css.perfilLinkBtn} ${css.perfilDanger}`}
                  onClick={alCancelarSuscripcion}
                  disabled={cancelarSuscripcion.isPending}
                >
                  {trd("cancelar_suscripcion", lang)}
                </button>
              </>
            )}

            {!c.is_pro && (
              <button
                className={css.perfilLinkBtn}
                onClick={() => {
                  onCerrar();
                  onVerPlanes();
                }}
              >
                {trd("ver_planes_perfil", lang)}
              </button>
            )}
          </div>
        </>
      )}
    </Modal>
  );
}
