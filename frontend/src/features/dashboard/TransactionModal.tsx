import { useEffect, useState } from "react";

import { ApiError } from "@/api/client";
import { useBorrarTx, useCrearRecurrente, useCrearTx, useEditarTx, useViajes } from "@/api/queries";
import type { Frecuencia, Moneda, Tipo, Transaccion } from "@/api/types";
import { Modal } from "@/components/Modal";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import { trd } from "./messages";
import css from "./Dashboard.module.css";

const MONEDAS: Moneda[] = ["ARS", "USD", "EUR"];
const MONEDA_LABEL: Record<Moneda, string> = { ARS: "$ ARS", USD: "USD", EUR: "€ EUR" };
const SUFIJO: Record<Moneda, string> = { ARS: "(ARS $)", USD: "(USD)", EUR: "(EUR €)" };

type Forma = {
  tipo: Tipo;
  moneda: Moneda;
  monto: string;
  fecha: string;
  categoria: string;
  descripcion: string;
  viajeId: string;
  recurrencia: Frecuencia | "no";
};

function formaVacia(): Forma {
  return {
    tipo: "Gasto",
    moneda: "ARS",
    monto: "",
    fecha: new Date().toISOString().split("T")[0],
    categoria: "",
    descripcion: "",
    viajeId: "",
    recurrencia: "no",
  };
}

function formaDesdeTx(t: Transaccion): Forma {
  return {
    tipo: t.tipo,
    moneda: t.moneda ?? "ARS",
    monto: String(t.monto),
    fecha: t.fecha,
    categoria: t.categoria ?? "",
    descripcion: t.descripcion ?? "",
    viajeId: t.viaje_id ? String(t.viaje_id) : "",
    recurrencia: "no",
  };
}

type Props = {
  abierto: boolean;
  editando: Transaccion | null;
  isPro: boolean;
  categoriasSugeridas: string[];
  onCerrar: () => void;
  onNecesitaPro: () => void;
};

export function TransactionModal({ abierto, editando, isPro, categoriasSugeridas, onCerrar, onNecesitaPro }: Props) {
  const { lang } = usePreferencias();
  const toast = useToast();
  const crear = useCrearTx();
  const editar = useEditarTx();
  const borrar = useBorrarTx();
  const crearRecurrente = useCrearRecurrente();
  // El select de viaje solo tiene sentido para cuentas Pro (Viajes es una
  // función Pro), y solo mientras el modal está realmente abierto.
  const viajes = useViajes(abierto && isPro);

  const [f, setF] = useState<Forma>(formaVacia);

  useEffect(() => {
    if (!abierto) return;
    setF(editando ? formaDesdeTx(editando) : formaVacia());
  }, [abierto, editando]);

  const set = (parcial: Partial<Forma>) => setF((prev) => ({ ...prev, ...parcial }));

  const enviando = crear.isPending || editar.isPending || crearRecurrente.isPending;

  async function alGuardar() {
    const monto = parseFloat(f.monto.replace(",", "."));
    if (!monto || monto <= 0) {
      toast(trd("monto_invalido", lang));
      return;
    }
    if (!f.fecha) {
      toast(trd("fecha_requerida", lang));
      return;
    }

    const payload = {
      tipo: f.tipo,
      monto,
      fecha: f.fecha,
      categoria: f.categoria.trim(),
      descripcion: f.descripcion.trim(),
      moneda: f.moneda,
      viaje_id: f.tipo === "Gasto" && f.viajeId ? Number(f.viajeId) : null,
    };

    try {
      if (editando) {
        await editar.mutateAsync({ id: editando.id, ...payload });
        toast(trd("tx_actualizada", lang));
        onCerrar();
        return;
      }
      if (f.recurrencia !== "no") {
        await crearRecurrente.mutateAsync({ ...payload, frecuencia: f.recurrencia });
        toast(trd("recurrente_creado", lang, { frecuencia: trd(f.recurrencia === "semanal" ? "frecuencia_semanal" : "frecuencia_mensual", lang) }));
        onCerrar();
        return;
      }
      await crear.mutateAsync(payload);
      toast(f.tipo === "Ingreso" ? trd("ingreso_guardado", lang) : trd("gasto_guardado", lang));
      onCerrar();
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        if (f.recurrencia !== "no") {
          // El límite del plan free bloqueó el recurrente: se ofrece Pro sin
          // cerrar este modal, para no perder lo que la persona ya cargó.
          onNecesitaPro();
          return;
        }
        if (err.message === "limite_pro") {
          toast(trd("limite_transacciones", lang));
        } else {
          toast(trd("sin_permiso", lang));
        }
        return;
      }
      toast(trd("error_guardar", lang));
    }
  }

  async function alEliminar() {
    if (!editando) return;
    if (!confirm(trd("confirm_borrar_tx", lang))) return;
    try {
      await borrar.mutateAsync(editando.id);
      toast(trd("tx_eliminada", lang));
      onCerrar();
    } catch {
      toast(trd("error_guardar", lang));
    }
  }

  return (
    <Modal
      abierto={abierto}
      titulo={editando ? trd("editar_transaccion", lang) : trd("nueva_transaccion", lang)}
      onCerrar={onCerrar}
      grande
    >
      <div className={css.tipoToggle}>
        <button
          className={`${css.tipoBtn} ${f.tipo === "Gasto" ? css.gastoActive : css.inactive}`}
          onClick={() => set({ tipo: "Gasto" })}
        >
          {trd("gasto", lang)}
        </button>
        <button
          className={`${css.tipoBtn} ${f.tipo === "Ingreso" ? css.ingresoActive : css.inactive}`}
          onClick={() => set({ tipo: "Ingreso", viajeId: "" })}
        >
          {trd("ingreso", lang)}
        </button>
      </div>

      <div className={css.monedaToggle}>
        {MONEDAS.map((m) => (
          <button key={m} className={`${css.monedaBtn} ${f.moneda === m ? css.active : ""}`} onClick={() => set({ moneda: m })}>
            {MONEDA_LABEL[m]}
          </button>
        ))}
      </div>

      <div className={css.campo}>
        <label htmlFor="tx-monto">
          {trd("monto_lbl", lang)} {SUFIJO[f.moneda]}
        </label>
        <input
          id="tx-monto"
          type="text"
          inputMode="decimal"
          placeholder="0,00"
          autoComplete="off"
          value={f.monto}
          onChange={(e) => set({ monto: e.target.value })}
        />
      </div>
      <div className={css.campo}>
        <label htmlFor="tx-fecha">Fecha</label>
        <input id="tx-fecha" type="date" value={f.fecha} onChange={(e) => set({ fecha: e.target.value })} />
      </div>
      <div className={css.campo}>
        <label htmlFor="tx-cat">Categoría</label>
        <input
          id="tx-cat"
          type="text"
          placeholder="Ej: Supermercado, Sueldo..."
          list="cat-suggestions-tx"
          autoComplete="off"
          value={f.categoria}
          onChange={(e) => set({ categoria: e.target.value })}
        />
        <datalist id="cat-suggestions-tx">
          {categoriasSugeridas.map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>
      </div>

      {isPro && f.tipo === "Gasto" && (
        <div className={css.campo}>
          <label htmlFor="tx-viaje">Viaje (opcional)</label>
          <select id="tx-viaje" value={f.viajeId} onChange={(e) => set({ viajeId: e.target.value })}>
            <option value="">Ninguno</option>
            {(viajes.data ?? []).map((v) => (
              <option key={v.id} value={v.id}>
                {v.nombre}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className={css.campo}>
        <label htmlFor="tx-desc">Descripción</label>
        <input
          id="tx-desc"
          type="text"
          placeholder="Descripción opcional"
          value={f.descripcion}
          onChange={(e) => set({ descripcion: e.target.value })}
        />
      </div>

      {!editando && (
        <div className={css.campo}>
          <label>Repetición</label>
          <div className={css.monedaToggle} style={{ marginTop: 4 }}>
            <button className={`${css.monedaBtn} ${f.recurrencia === "no" ? css.active : ""}`} onClick={() => set({ recurrencia: "no" })}>
              Sin repetir
            </button>
            <button className={`${css.monedaBtn} ${f.recurrencia === "semanal" ? css.active : ""}`} onClick={() => set({ recurrencia: "semanal" })}>
              Semanal
            </button>
            <button className={`${css.monedaBtn} ${f.recurrencia === "mensual" ? css.active : ""}`} onClick={() => set({ recurrencia: "mensual" })}>
              Mensual
            </button>
          </div>
        </div>
      )}

      <button className={css.btnGuardar} onClick={alGuardar} disabled={enviando}>
        Guardar
      </button>
      {editando && (
        <button className={`${css.btnGuardar} ${css.btnEliminarTx}`} onClick={alEliminar}>
          Eliminar
        </button>
      )}
    </Modal>
  );
}
