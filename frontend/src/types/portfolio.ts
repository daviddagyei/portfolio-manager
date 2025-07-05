import { BaseEntity } from './base';

export enum PortfolioType {
  PERSONAL = 'personal',
  RETIREMENT = 'retirement',
  EDUCATION = 'education',
  INVESTMENT = 'investment',
  TRADING = 'trading',
  OTHER = 'other'
}

export interface Portfolio extends BaseEntity {
  name: string;
  description?: string;
  portfolioType: PortfolioType;
  userId: number;
  initialValue: number;
  currentValue: number;
  totalReturn: number;
  totalReturnPercentage: number;
  targetReturn?: number;
  riskTolerance?: string;
  isActive: boolean;
}

export interface PortfolioCreate {
  name: string;
  description?: string;
  portfolioType: PortfolioType;
  initialValue: number;
  targetReturn?: number;
  riskTolerance?: string;
}

export interface PortfolioUpdate {
  name?: string;
  description?: string;
  portfolioType?: PortfolioType;
  targetReturn?: number;
  riskTolerance?: string;
}

export interface PortfolioSummary {
  id: number;
  name: string;
  portfolioType: PortfolioType;
  currentValue: number;
  totalReturn: number;
  totalReturnPercentage: number;
  assetCount: number;
  lastUpdated: string;
}

export interface PortfolioSearchParams {
  userId?: number;
  portfolioType?: PortfolioType;
  page?: number;
  perPage?: number;
}

export interface PortfolioHolding extends BaseEntity {
  portfolioId: number;
  assetId: number;
  quantity: number;
  averageCost: number;
  currentPrice?: number;
  marketValue: number;
  unrealizedGainLoss: number;
  unrealizedGainLossPercentage: number;
  asset?: {
    symbol: string;
    name: string;
    assetType: string;
  };
}
