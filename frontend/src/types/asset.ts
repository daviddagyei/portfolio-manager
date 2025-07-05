import { BaseEntity } from './base';

export enum AssetType {
  STOCK = 'stock',
  BOND = 'bond',
  ETF = 'etf',
  MUTUAL_FUND = 'mutual_fund',
  CRYPTOCURRENCY = 'cryptocurrency',
  COMMODITY = 'commodity',
  REAL_ESTATE = 'real_estate',
  CASH = 'cash',
  OTHER = 'other'
}

export interface Asset extends BaseEntity {
  symbol: string;
  name: string;
  assetType: AssetType;
  sector?: string;
  industry?: string;
  description?: string;
  isActive: boolean;
}

export interface AssetCreate {
  symbol: string;
  name: string;
  assetType: AssetType;
  sector?: string;
  industry?: string;
  description?: string;
}

export interface AssetUpdate {
  name?: string;
  sector?: string;
  industry?: string;
  description?: string;
}

export interface AssetSearchParams {
  symbol?: string;
  assetType?: AssetType;
  sector?: string;
  search?: string;
  page?: number;
  perPage?: number;
}
