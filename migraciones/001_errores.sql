-- Registro de errores del frontend y del backend (ver routes_errores.py).
--
-- Aplicada en producción el 2026-09-04.
--
-- Es idempotente: se puede correr de nuevo sin romper nada, y sirve para
-- levantar la base desde cero.

CREATE TABLE IF NOT EXISTS public.errores (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  creado_en   timestamptz NOT NULL DEFAULT now(),
  -- 'frontend' = lo reportó el navegador; 'backend' = lo agarró el error 500.
  origen      text NOT NULL CHECK (origen IN ('frontend', 'backend')),
  mensaje     text NOT NULL,
  stack       text,
  ruta        text,
  -- Si se borra la cuenta, el error queda pero sin dueño: sirve igual para
  -- diagnosticar y no bloquea el borrado.
  user_id     uuid REFERENCES public.usuarios(id) ON DELETE SET NULL,
  user_agent  text
);

-- Las consultas siempre son "los últimos errores".
CREATE INDEX IF NOT EXISTS errores_creado_en_idx ON public.errores (creado_en DESC);

-- Misma política permisiva que el resto de las tablas: el aislamiento por
-- usuario lo hace Flask con la sesión, no Postgres (ver el resto del esquema).
ALTER TABLE public.errores ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS acceso_total ON public.errores;
CREATE POLICY acceso_total ON public.errores FOR ALL USING (true) WITH CHECK (true);
