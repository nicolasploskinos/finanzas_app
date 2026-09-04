import { useBorrarEjemplos } from "@/api/queries";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import css from "./Dashboard.module.css";
import { trd } from "./messages";

/**
 * Aviso de que los movimientos que se ven son los de ejemplo que se siembran
 * al registrarse (ver sembrar_ejemplos en routes_auth.py).
 *
 * Deja explícito que son de prueba —para que nadie los confunda con datos
 * propios— y da la salida en un solo toque. Desaparece solo en cuanto no
 * queda ninguno.
 */
export function EjemplosBanner() {
  const { lang } = usePreferencias();
  const toast = useToast();
  const borrar = useBorrarEjemplos();

  async function alBorrar() {
    try {
      await borrar.mutateAsync();
      toast(trd("ejemplos_borrados", lang));
    } catch {
      toast(trd("error_guardar", lang));
    }
  }

  return (
    <div className={css.avisoEjemplos}>
      <span>{trd("ejemplos_aviso", lang)}</span>
      <button onClick={alBorrar} disabled={borrar.isPending}>
        {trd("ejemplos_borrar", lang)}
      </button>
    </div>
  );
}
