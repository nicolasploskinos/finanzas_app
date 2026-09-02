import { LegalPage } from "./LegalPage";
import { ACTUALIZADO, INTRO, SECCIONES, TITULO } from "./terminosContent";

export function TerminosPage() {
  return <LegalPage titulo={TITULO} actualizado={ACTUALIZADO} intro={INTRO} secciones={SECCIONES} />;
}
