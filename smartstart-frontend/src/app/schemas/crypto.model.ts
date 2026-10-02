// schemas/crypto.model.ts

// ── INPUT ──────────────────────────────────────
export interface CryptoRequest {
    societe: string;
    ticker: string;
    jours: number;
    horizon: number;
    budget: number;
}

// ── BUDGET ─────────────────────────────────────
export interface BudgetAnalysis {
    budget: number;
    nb_crypto_achetable: number;
    investissement_recommande: number;
    nb_crypto_recommande: number;
    gain_potentiel: number;
    perte_max_estimee: number;
    pourcentage_investir: number;
    conseil: string;
}

// ── OUTPUT ─────────────────────────────────────
export interface CryptoResult {
    societe: string;
    crypto_nom: string;
    crypto_symbol: string;
    date_analyse: string;
    jours_analyses: number;
    horizon: number;

    signal_final: 'BUY' | 'SELL' | 'HOLD';
    score_confiance: number;
    niveau_confiance: string;
    interpretation: string;

    modeles: ModelResult[];
    stats: CryptoStats;
    forecast: ForecastResult;
    prob_hausse: number;
    historique: HistoriqueData;
    synthese: string;
    tableau_stats: TableauRow[];
    budget_analysis: BudgetAnalysis | null;
}

export interface ModelResult {
    nom: string;
    cours: string;
    signal: 'BUY' | 'SELL' | 'NEUTRAL' | 'HOLD';
    detail: string;
    confiance: number;
}

export interface CryptoStats {
    prix_actuel: number;
    prix_min: number;
    prix_max: number;
    rendement_total: number;
    vol_moy_7j: number;
    vol_moy_30j: number;
    vol_niveau: string;
    return_moyen: number;
    return_sd: number;
    adf_pvalue: number;
    adf_stationary: boolean;
}

export interface ForecastResult {
    prix_predit: number;
    variation: number;
    dates: string[];
    mean: number[];
    lo_80: number;
    hi_80: number;
    lo_95: number;
    hi_95: number;
}

export interface HistoriqueData {
    dates: string[];
    prix: number[];
    vol_7j: (number | null)[];
    vol_30j: (number | null)[];
    prob_hausse: (number | null)[];
}

export interface TableauRow {
    indicateur: string;
    valeur: string;
    positive?: boolean;
}