import { useEffect } from "react";

/** Agrega una clase a <body> mientras el componente que llama está montado
 *  (y la saca al desmontar). Se usa para que las páginas con el tema Nébula
 *  ocupen todo el ancho de pantalla sin tocar el límite global de `body`
 *  que sigue usando el resto de la app — ver nebula.module.css. */
export function useFullBleed(claseCss: string) {
  useEffect(() => {
    document.body.classList.add(claseCss);
    return () => document.body.classList.remove(claseCss);
  }, [claseCss]);
}
