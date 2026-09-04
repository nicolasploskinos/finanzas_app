import { useState } from "react";

import { useWhatsappCodigo, useWhatsappDesvincular, useWhatsappEstado } from "@/api/queries";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import { AccBody } from "./AccBody";
import { trd } from "./messages";
import css from "./Dashboard.module.css";
import { useConfirmar } from "@/components/Confirmacion";

export function WhatsappCard({ abierto, onToggle }: { abierto: boolean; onToggle: () => void }) {
  const { lang } = usePreferencias();
  const confirmar = useConfirmar();
  const toast = useToast();
  const estado = useWhatsappEstado(abierto);
  const codigo = useWhatsappCodigo();
  const desvincular = useWhatsappDesvincular();
  const [codigoInfo, setCodigoInfo] = useState<{ codigo: string; wa_link: string } | null>(null);

  async function generarCodigo() {
    try {
      const d = await codigo.mutateAsync();
      if (!d.ok) {
        toast(trd("wa_codigo_error", lang));
        return;
      }
      setCodigoInfo({ codigo: d.codigo, wa_link: d.wa_link });
    } catch {
      toast(trd("wa_codigo_error", lang));
    }
  }

  async function alDesvincular() {
    const ok = await confirmar({
      titulo: trd("dlg_desvincular_t", lang),
      confirmar: trd("dlg_desvincular_b", lang),
      cancelar: trd("dlg_cancelar", lang),
      peligro: true,
    });
    if (!ok) return;
    await desvincular.mutateAsync();
    setCodigoInfo(null);
    toast(trd("wa_desvinculado", lang));
  }

  const vinculado = estado.data?.vinculado ?? false;
  const telefonoOculto = estado.data && estado.data.vinculado ? estado.data.telefono_oculto : "";

  return (
    <div className={`${css.cotWrap} ${css.cotWrapWhatsapp}`}>
      <div className={css.cotHeader} onClick={onToggle}>
        <span>{trd("whatsapp_titulo", lang)}</span>
        <span className={css.chev}>{abierto ? "▲" : "▼"}</span>
      </div>
      <AccBody open={abierto}>
        {vinculado ? (
          <div>
            <p className={css.waVinculadoP}>
              {trd("wa_vinculado_a", lang)} <strong>{telefonoOculto}</strong>
            </p>
            <p className={css.waVinculadoSub}>{trd("wa_probar_pregunta", lang)}</p>
            <button className={`${css.btnGuardar} ${css.waBtnDesvincular}`} onClick={alDesvincular}>
              {trd("desvincular", lang)}
            </button>
          </div>
        ) : (
          <div>
            <p className={css.waTexto}>{trd("wa_intro", lang)}</p>
            <button className={css.btnGuardar} style={{ margin: 0 }} onClick={generarCodigo} disabled={codigo.isPending}>
              {trd("vincular_whatsapp", lang)}
            </button>
            {codigoInfo && (
              <div className={css.waCodigoBox}>
                <div className={css.waCodigoLabel}>{trd("wa_tocar_para_abrir", lang)}</div>
                <a className={css.waLink} href={codigoInfo.wa_link} target="_blank" rel="noopener">
                  {trd("abrir_whatsapp", lang)}
                </a>
                <div className={css.waVence}>
                  {trd("wa_codigo", lang)} <strong>{codigoInfo.codigo}</strong> · {trd("wa_vence", lang)}
                </div>
              </div>
            )}
          </div>
        )}
      </AccBody>
    </div>
  );
}
