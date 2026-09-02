/** Error de una respuesta HTTP no-2xx. `status` permite distinguir el 401. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// El 401 de estas dos rutas es parte normal de su contrato (credenciales
// inválidas), no una sesión vencida — así que no dispara el redirect global.
// Si no se excluyeran, un intento de login fallido rebotaría a /montor/login
// (donde ya estás) en vez de mostrar el error en el formulario.
const RUTAS_PUBLICAS_CON_401_ESPERADO = ["/api/montor/login", "/api/montor/register"];

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: "same-origin",
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });

  if (!res.ok) {
    // La sesión de Flask vive en una cookie; si venció, la API contesta 401
    // y el lugar donde hay que volver es el login del servidor.
    if (res.status === 401 && !RUTAS_PUBLICAS_CON_401_ESPERADO.includes(path)) {
      window.location.href = "/montor/login";
    }
    let detalle = res.statusText;
    try {
      const cuerpo = (await res.json()) as { error?: string };
      if (cuerpo?.error) detalle = cuerpo.error;
    } catch {
      /* respuesta sin JSON: nos quedamos con el statusText */
    }
    throw new ApiError(detalle, res.status);
  }

  return (await res.json()) as T;
}

export const api = {
  get: <T,>(path: string) => request<T>(path),
  post: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  del: <T,>(path: string) => request<T>(path, { method: "DELETE" }),
};
