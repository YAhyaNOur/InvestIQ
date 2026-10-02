import { HttpErrorResponse } from '@angular/common/http';

const FIELD_LABELS: Record<string, string> = {
  username: "Nom d'utilisateur",
  email: 'Email',
  password: 'Mot de passe',
  full_name: 'Nom complet',
  role: 'Rôle',
};

/**
 * Transforme n'importe quelle erreur HTTP en message lisible pour l'utilisateur.
 * Gère : serveur éteint, detail texte (409, 401...), liste de validation (422), erreur 500.
 */
export function apiErrorMessage(err: unknown, fallback = 'Une erreur est survenue. Réessayez.'): string {
  const e = err as HttpErrorResponse;

  if (!e || e.status === 0) {
    return 'Impossible de joindre le serveur. Vérifiez que le backend est lancé (port 8000).';
  }

  const detail = e.error?.detail;

  // 422 : liste d'erreurs de validation FastAPI
  if (Array.isArray(detail)) {
    const messages = detail.map((d: any) => {
      const field = d?.loc?.[d.loc.length - 1];
      const label = FIELD_LABELS[field] ?? field;
      let msg: string = String(d?.msg ?? 'valeur invalide').replace(/^Value error, /, '');
      if (msg.includes('email address')) msg = 'adresse email invalide';
      return label && !msg.toLowerCase().startsWith(String(label).toLowerCase()) ? `${label} : ${msg}` : msg;
    });
    return messages.join(' · ');
  }

  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (e.status === 401) return 'Session expirée ou identifiants incorrects.';
  if (e.status === 403) return "Accès refusé pour ce compte.";
  if (e.status === 404) return 'Ressource introuvable.';
  if (e.status >= 500) return `Erreur du serveur (${e.status}). Regardez le terminal du backend.`;

  return fallback;
}
