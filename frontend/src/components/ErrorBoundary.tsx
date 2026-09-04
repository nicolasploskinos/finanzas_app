import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

import { reportarError } from "@/lib/reportarError";
import css from "./ErrorBoundary.module.css";

type Props = { children: ReactNode };
type State = { rota: boolean };

/**
 * Red de contención para un error de render.
 *
 * Sin esto, una excepción en cualquier componente desmonta el árbol entero y
 * el usuario se queda mirando una pantalla en blanco, sin saber si fue él,
 * la conexión o la app — y nosotros sin enterarnos nunca. Acá se muestra algo
 * legible con una salida, y se manda el error al server.
 *
 * Tiene que ser una clase: es la única forma de implementar
 * componentDidCatch, React no expone un equivalente en hooks.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { rota: false };

  static getDerivedStateFromError(): State {
    return { rota: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    reportarError(error, info.componentStack ?? undefined);
  }

  render() {
    if (!this.state.rota) return this.props.children;

    return (
      <div className={css.pantalla}>
        <div className={css.caja}>
          <div className={css.icono}>😵</div>
          <h1>Se nos rompió esta pantalla</h1>
          <p>
            No es culpa tuya y tus datos están a salvo. Ya nos llegó el aviso y lo vamos a
            revisar.
          </p>
          {/* Recarga dura a propósito: el estado de React quedó en un punto
              inconsistente, así que no alcanza con volver a montar. */}
          <button onClick={() => window.location.reload()}>Recargar</button>
          <a href="/montor">Volver al inicio</a>
        </div>
      </div>
    );
  }
}
