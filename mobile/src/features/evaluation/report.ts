import type { ProfileId } from "@/demo/types";
export const modelOptions = [
  "Média histórica",
  "Último valor",
  "Sazonal semanal",
  "Modelo AgiPrevê",
] as const;
export const metricDefinitions = [
  ["MAE", "Erro absoluto médio, em reais."],
  ["MSE", "Erro quadrático médio, em reais ao quadrado."],
  ["RMSE", "Raiz do erro quadrático médio, em reais."],
  [
    "WAPE",
    "Erro absoluto ponderado; indefinido quando a soma absoluta dos realizados é zero.",
  ],
  [
    "Bias",
    "Média de previsto menos realizado; sinal positivo indica superestimação.",
  ],
  [
    "Precisão de risco",
    "Proporção dos alertas que corresponderam a insuficiência financeira.",
  ],
  [
    "Recall de risco",
    "Proporção dos casos de insuficiência identificados previamente.",
  ],
  [
    "F1 de risco",
    "Equilíbrio entre precisão e recall, com casos indefinidos explicitados.",
  ],
] as const;
export interface ExperimentConfig {
  profile: ProfileId;
  seed: number;
  horizon: number;
  model: string;
  cutoff: string;
}
export function prepareReport(config: ExperimentConfig) {
  return {
    schemaVersion: "ui-preview-1",
    status: "awaiting_backend" as const,
    syntheticData: true,
    datasetVersion: "ui-fixture-1",
    configuration: config,
    temporalPolicy:
      "Training data must end at the cutoff; realized future data is evaluation-only.",
    evaluation: {
      method: "rolling-origin",
      models: [...modelOptions],
      horizons: [7, 15, 30],
    },
    metrics: Object.fromEntries(
      metricDefinitions.map(([name]) => [name, null]),
    ),
    recalculationP95Ms: null,
    performanceTargetMs: 2000,
    note: "Configuration preview only. No experiment, training or backtest has been executed.",
  };
}
