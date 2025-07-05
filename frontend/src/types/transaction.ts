import { BaseEntity } from './base';

export enum TransactionType {
  BUY = 'buy',
  SELL = 'sell',
  DIVIDEND = 'dividend',
  SPLIT = 'split',
  TRANSFER_IN = 'transfer_in',
  TRANSFER_OUT = 'transfer_out',
  FEE = 'fee',
  INTEREST = 'interest'
}

export interface Transaction extends BaseEntity {
  userId: number;
  portfolioId: number;
  assetId: number;
  transactionType: TransactionType;
  quantity: number;
  price: number;
  totalAmount: number;
  fees: number;
  transactionDate: string;
  notes?: string;
}

export interface TransactionCreate {
  portfolioId: number;
  assetId: number;
  transactionType: TransactionType;
  quantity: number;
  price: number;
  totalAmount: number;
  fees?: number;
  transactionDate: string;
  notes?: string;
}

export interface TransactionUpdate {
  quantity?: number;
  price?: number;
  totalAmount?: number;
  fees?: number;
  transactionDate?: string;
  notes?: string;
}

export interface TransactionWithDetails extends Transaction {
  assetSymbol: string;
  assetName: string;
  portfolioName: string;
}

export interface TransactionSearchParams {
  portfolioId?: number;
  assetId?: number;
  transactionType?: TransactionType;
  startDate?: string;
  endDate?: string;
  page?: number;
  perPage?: number;
}
