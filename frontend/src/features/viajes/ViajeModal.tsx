import { useEffect, useState } from "react";

import { useGuardarViaje } from "@/api/queries";
import type { Viaje } from "@/api/types";
import { Modal } from "@/components/Modal";
import { usePreferencias } from "@/hooks/usePreferencias";
import { useToast } from "@/hooks/useToast";
import css from "./Viajes.module.css";

type Props = {
  abierto: boolean;
  /** El viaje a editar, o null para crear uno nuevo. */
  viaje: Viaje | null;
  onCerrar: () => void;
  onGuardado: (viaje: Viaje) => void;
};

const VACIO = { nombre: "", fecha_inicio: "", fecha_fin: "" };

export function ViajeModal({ abierto, viaje, onCerrar, onGuardado }: Props) {
  const { t } = usePreferencias();
  const toast = useToast();
  const guardar = useGuardarViaje();
  const [form, setForm] = useState(VACIO);

  // Al abrir se rellena con el viaje que se está editando (o se vacía si es
  // uno nuevo). Va acá y no en el onClick del botón para que el modal sea la
  // única fuente de su propio estado.
  useEffect(() => {
    if (!abierto) return;
    setForm(
      viaje
        ? { nombre: viaje.nombre, fecha_inicio: viaje.fecha_inicio, fecha_fin: viaje.fecha_fin }
        : VACIO,
    );
  }, [abierto, viaje]);

  const campo = (k: keyof typeof VACIO) => ({
    value: form[k],
    onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value })),
  });

  async function alGuardar() {
    const nombre = form.nombre.trim();
    if (!nombre || !form.fecha_inicio || !form.fecha_fin) {
      toast(t("missing_trip_fields"));
      return;
    }
    // Comparación de strings YYYY-MM-DD: el orden lexicográfico coincide con
    // el cronológico, así que no hace falta parsear.
    if (form.fecha_fin < form.fecha_inicio) {
      toast(t("fecha_hasta_invalida"));
      return;
    }

    try {
      const guardado = await guardar.mutateAsync({ ...form, nombre, id: viaje?.id });
      toast(t("viaje_guardado"));
      onCerrar();
      onGuardado(guardado);
    } catch {
      toast(t("error_guardar_viaje"));
    }
  }

  return (
    <Modal
      abierto={abierto}
      titulo={viaje ? t("editar_viaje") : t("nuevo_viaje")}
      onCerrar={onCerrar}
    >
      {/* En <form> para que Enter (o la tecla "Ir" del teclado del celular)
          guarde, sin tener que ir hasta el botón. Los demás botones llevan
          type="button" a propósito: sin eso enviarían el formulario. */}
      <form onSubmit={(e) => { e.preventDefault(); alGuardar(); }}>
      <div className={css.campo}>
        <label htmlFor="viaje-nombre">{t("nombre")}</label>
        <input id="viaje-nombre" type="text" placeholder={t("ejemplo_viaje")} {...campo("nombre")} />
      </div>
      <div className={css.campoRow}>
        <div className={css.campo}>
          <label htmlFor="viaje-desde">{t("desde")}</label>
          <input id="viaje-desde" type="date" {...campo("fecha_inicio")} />
        </div>
        <div className={css.campo}>
          <label htmlFor="viaje-hasta">{t("hasta")}</label>
          <input id="viaje-hasta" type="date" {...campo("fecha_fin")} />
        </div>
      </div>
        <button type="submit" className={css.btnGuardar} disabled={guardar.isPending}>
        {guardar.isPending ? t("guardando") : t("guardar_viaje")}
      </button>
      </form>
    </Modal>
  );
}
