# Migraciones

Cambios de esquema de la base, en orden. Cada archivo es **idempotente**
(`IF NOT EXISTS`), así que correrlos de nuevo no rompe nada y sirven para
levantar la base desde cero.

## Por qué la app no las aplica sola

`montor_server.py` se conecta con la clave **anon** de Supabase, que va contra
PostgREST y **no puede ejecutar DDL** — no hay forma de que la app se cree una
tabla al arrancar. Darle credenciales de administrador sólo para eso sería
empeorar la seguridad de toda la app a cambio de ahorrar un paso manual que se
hace una vez por migración.

Consecuencia práctica: si una tabla falta, el código que la usa tiene que
degradar sin romperse. `routes_errores.registrar()` ya lo hace — si el insert
falla, escribe en el log del server y sigue.

## Cómo aplicar una

**Opción A — panel de Supabase** (la más simple): SQL Editor → pegar el
contenido del archivo → Run.

**Opción B — desde acá**, con el pooler:

```bash
python - <<'FIN'
import io, psycopg2
from urllib.parse import quote
DSN = ("postgresql://postgres.qctlaozwqbznshwhgnvj:" + quote("LA_PASSWORD")
       + "@aws-1-sa-east-1.pooler.supabase.com:5432/postgres")
con = psycopg2.connect(DSN, connect_timeout=20); con.autocommit = True
con.cursor().execute(io.open("migraciones/001_errores.sql", encoding="utf-8").read())
print("aplicada")
FIN
```

Ojo con el host: el viejo `db.<ref>.supabase.co` **ya no resuelve**, Supabase
lo movió al pooler. Y es `aws-1-sa-east-1`, no `aws-0`.

## Aplicadas

| Archivo | Qué hace | Estado |
|---|---|---|
| `001_errores.sql` | Tabla `errores` para el registro de fallas | Aplicada en producción, 2026-09-04 |
