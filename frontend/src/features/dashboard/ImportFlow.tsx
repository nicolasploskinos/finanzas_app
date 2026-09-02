import { useRef, useState } from "react";

import { ApiError } from "@/api/client";
import { useImportConfirm, useImportPreview } from "@/api/queries";
import type { ImportRow } from "@/api/types";
import { Modal } from "@/components/Modal";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import { fmtMon } from "@/lib/formato";
import { trd } from "./messages";
import type { DashMsgKey } from "./messages";
import css from "./Dashboard.module.css";

const CODIGOS_ERROR_IMPORT = new Set<DashMsgKey>([
  "invalid_file_type",
  "cant_read_file",
  "empty_file",
  "unrecognized_columns",
  "nothing_to_import",
  "too_many_transactions",
  "nothing_valid_to_import",
]);
function esCodigoConocido(codigo: string): codigo is DashMsgKey {
  return CODIGOS_ERROR_IMPORT.has(codigo as DashMsgKey);
}

type Props = {
  isPro: boolean;
  onNecesitaPro: () => void;
};

/** Botón "Importar" del panel + todo el flujo de preview/confirmación. Vive
 *  como un componente aparte (no solo un botón) porque el input de archivo,
 *  el modal de preview y las dos mutations están todos acoplados entre sí. */
export function ImportFlow({ isPro, onNecesitaPro }: Props) {
  const { lang } = usePreferencias();
  const toast = useToast();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const preview = useImportPreview();
  const confirmar = useImportConfirm();

  const [filas, setFilas] = useState<ImportRow[]>([]);
  const [errores, setErrores] = useState(0);
  const [seleccion, setSeleccion] = useState<Set<number>>(new Set());
  const [categoria, setCategoria] = useState("");
  const [abierto, setAbierto] = useState(false);

  function trigger() {
    if (!isPro) {
      onNecesitaPro();
      return;
    }
    if (inputRef.current) inputRef.current.value = "";
    inputRef.current?.click();
  }

  async function alElegirArchivo(e: React.ChangeEvent<HTMLInputElement>) {
    const archivo = e.target.files?.[0];
    if (!archivo) return;
    toast(trd("leyendo_archivo", lang));
    try {
      const data = await preview.mutateAsync(archivo);
      if (!data.transacciones.length) {
        toast(trd("no_encontraron_movimientos", lang));
        return;
      }
      setFilas(data.transacciones);
      setErrores(data.errores);
      setSeleccion(new Set(data.transacciones.map((_, i) => i)));
      setCategoria("");
      setAbierto(true);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        onNecesitaPro();
        return;
      }
      const codigo = err instanceof ApiError ? err.message : "no_se_pudo_leer_archivo";
      toast(trd("error_con_codigo", lang, { detalle: esCodigoConocido(codigo) ? trd(codigo, lang) : codigo }));
    }
  }

  function toggleFila(i: number) {
    setSeleccion((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  async function confirmarImport() {
    const cat = categoria.trim();
    const elegidas = filas.filter((_, i) => seleccion.has(i)).map((t) => ({ ...t, categoria: cat || t.categoria }));
    if (!elegidas.length) {
      toast(trd("elegi_movimiento", lang));
      return;
    }
    try {
      const data = await confirmar.mutateAsync(elegidas);
      setAbierto(false);
      toast(trd("movimientos_importados", lang, { n: data.insertados }));
    } catch (err) {
      const codigo = err instanceof ApiError ? err.message : "no_pudo_importar";
      toast(trd("error_con_codigo", lang, { detalle: esCodigoConocido(codigo) ? trd(codigo, lang) : codigo }));
    }
  }

  return (
    <>
      <button className={css.importExportBtn} onClick={trigger}>
        {trd("importar", lang)}
      </button>
      <input ref={inputRef} type="file" accept=".csv" style={{ display: "none" }} onChange={alElegirArchivo} />

      <Modal
        abierto={abierto}
        titulo={lang === "en" ? "Import transactions" : "Importar movimientos"}
        onCerrar={() => setAbierto(false)}
        grande
      >
        <p className={css.importResumen}>
          {trd("movimientos_encontrados", lang, { n: filas.length })}
          {errores > 0 ? " · " + trd("filas_no_reconocidas", lang, { n: errores }) : ""}
        </p>
        <div className={css.campo}>
          <label>{lang === "en" ? "Category (optional, applies to all selected)" : "Categoría (opcional, se aplica a todos los seleccionados)"}</label>
          <input
            type="text"
            placeholder={lang === "en" ? "E.g.: Imported" : "Ej: Importado"}
            autoComplete="off"
            value={categoria}
            onChange={(e) => setCategoria(e.target.value)}
          />
        </div>
        <div className={css.importLista}>
          {filas.map((t, i) => (
            <label key={i} className={css.importItem}>
              <input type="checkbox" checked={seleccion.has(i)} onChange={() => toggleFila(i)} />
              <span style={{ flex: 1 }}>
                <strong>{t.fecha}</strong> · {t.tipo === "Gasto" ? "🔴" : "🟢"} {fmtMon(t.monto, t.moneda)}
                {t.descripcion && (
                  <>
                    <br />
                    <span className={css.desc}>{t.descripcion}</span>
                  </>
                )}
              </span>
            </label>
          ))}
        </div>
        <button className={css.btnGuardar} onClick={confirmarImport} disabled={confirmar.isPending}>
          {lang === "en" ? "Import selected" : "Importar seleccionados"}
        </button>
      </Modal>
    </>
  );
}
