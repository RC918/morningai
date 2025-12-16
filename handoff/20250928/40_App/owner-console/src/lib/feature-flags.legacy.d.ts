export function isFeatureEnabled(feature: string): boolean;

export function getAvailableFeatures(): string[];

export const AVAILABLE_FEATURES: {
  readonly DASHBOARD: 'dashboard';
  readonly STRATEGIES: 'strategies';
  readonly APPROVALS: 'approvals';
  readonly HISTORY: 'history';
  readonly COSTS: 'costs';
  readonly SETTINGS: 'settings';
  readonly CHECKOUT: 'checkout';
};
