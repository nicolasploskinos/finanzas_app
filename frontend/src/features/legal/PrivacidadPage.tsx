import { LegalPage } from "./LegalPage";
import { ACTUALIZADO, INTRO, SECCIONES, TITULO } from "./privacidadContent";

export function PrivacidadPage() {
  return <LegalPage titulo={TITULO} actualizado={ACTUALIZADO} intro={INTRO} secciones={SECCIONES} />;
}
