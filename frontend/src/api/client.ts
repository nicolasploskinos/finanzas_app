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

async function leerDetalleError(res: Response): Promise<string> {
  try {
    const cuerpo = (await res.json()) as { error?: string };
    return cuerpo?.error ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const esFormData = init?.body instanceof FormData;
  const res = await fetch(path, {
    credentials: "same-origin",
    // Con FormData no se fija Content-Type a mano: el browser le agrega el
    // boundary del multipart solo, y pisarlo rompería el parseo en el server.
    headers: init?.body && !esFormData ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });

  if (!res.ok) {
    // La sesión de Flask vive en una cookie; si venció, la API contesta 401
    // y el lugar donde hay que volver es el login del servidor.
    if (res.status === 401 && !RUTAS_PUBLICAS_CON_401_ESPERADO.includes(path)) {
      window.location.href = "/montor/login";
    }
    throw new ApiError(await leerDetalleError(res), res.status);
  }

  return (await res.json()) as T;
}

export const api = {
  get: <T,>(path: string) => request<T>(path),
  post: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  /** Para subir archivos (import de CSV): manda FormData tal cual. */
  postForm: <T,>(path: string, form: FormData) => request<T>(path, { method: "POST", body: form }),
  put: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  del: <T,>(path: string) => request<T>(path, { method: "DELETE" }),
  /** Para exportar (Excel/PDF): la respuesta es el archivo, no JSON. */
  async getBlob(path: string): Promise<Blob> {
    const res = await fetch(path, { credentials: "same-origin" });
    if (!res.ok) {
      if (res.status === 401) window.location.href = "/montor/login";
      throw new ApiError(await leerDetalleError(res), res.status);
    }
    return res.blob();
  },
};
