import { useState } from "react";

import { api, ApiError } from "@/api/client";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

type Props = { isPro: boolean; onNecesitaPro: () => void };

export function ExportMenu({ isPro, onNecesitaPro }: Props) {
  const { lang } = usePreferencias();
  const toast = useToast();
  const [abierto, setAbierto] = useState(false);

  function toggle() {
    if (!isPro) {
      onNecesitaPro();
      return;
    }
    setAbierto((v) => !v);
  }

  async function exportar(formato: "excel" | "pdf") {
    setAbierto(false);
    try {
      const blob = await api.getBlob(`/api/montor/export/${formato}`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `montor.${formato === "excel" ? "xlsx" : "pdf"}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        onNecesitaPro();
        return;
      }
      toast(trd("no_pudo_exportar", lang));
    }
  }

  return (
    <div style={{ position: "relative" }}>
      <button className={css.importExportBtn} onClick={toggle}>
        {trd("exportar", lang)}
      </button>
      {abierto && (
        <>
          {/* Fondo invisible para cerrar el menú al clickear afuera, sin
              necesitar un listener global en document. */}
          <div style={{ position: "fixed", inset: 0, zIndex: 40 }} onClick={() => setAbierto(false)} />
          <div className={css.exportMenu}>
            <button className={css.exportMenuItem} onClick={() => exportar("excel")}>
              📊 Excel (.xlsx)
            </button>
            <button className={css.exportMenuItem} onClick={() => exportar("pdf")}>
              📄 PDF
            </button>
          </div>
        </>
      )}
    </div>
  );
}
