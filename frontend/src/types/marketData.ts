import { BaseEntity } from './base';

export interface PriceData extends BaseEntity {
  assetId: number;
  date: string;
  openPrice: number;
  highPrice: number;
  lowPrice: number;
  closePrice: number;
  volume?: number;
  adjustedClose?: number;
}

export interface PriceDataCreate {
  assetId: number;
  date: string;
  openPrice: number;
  highPrice: number;
  lowPrice: number;
  closePrice: number;
  volume?: number;
  adjustedClose?: number;
}

export interface PriceDataWithAsset extends PriceData {
  assetSymbol: string;
  assetName: string;
}

export interface PriceHistoryRequest {
  assetId: number;
  startDate?: string;
  endDate?: string;
  period?: string;
}

export interface PriceHistoryResponse {
  success: boolean;
  data: PriceData[];
  assetSymbol: string;
  assetName: string;
  period: string;
  totalRecords: number;
  message?: string;
}

export interface MarketDataSearchParams {
  assetId?: number;
  startDate?: string;
  endDate?: string;
  page?: number;
  perPage?: number;
}
