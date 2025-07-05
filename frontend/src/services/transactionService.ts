import apiClient from './apiClient';
import { 
  Transaction, 
  TransactionCreate, 
  TransactionUpdate, 
  TransactionWithDetails,
  TransactionSearchParams,
  ApiResponse,
  PaginatedResponse
} from '../types';

class TransactionService {
  private endpoint = '/transactions';

  async getTransactions(params?: TransactionSearchParams): Promise<PaginatedResponse<TransactionWithDetails>> {
    const response = await apiClient.get(this.endpoint, { params });
    return response.data;
  }

  async getTransaction(id: number): Promise<ApiResponse<Transaction>> {
    const response = await apiClient.get(`${this.endpoint}/${id}`);
    return response.data;
  }

  async createTransaction(transaction: TransactionCreate): Promise<ApiResponse<Transaction>> {
    const response = await apiClient.post(this.endpoint, transaction);
    return response.data;
  }

  async updateTransaction(id: number, transaction: TransactionUpdate): Promise<ApiResponse<Transaction>> {
    const response = await apiClient.put(`${this.endpoint}/${id}`, transaction);
    return response.data;
  }

  async deleteTransaction(id: number): Promise<ApiResponse<void>> {
    const response = await apiClient.delete(`${this.endpoint}/${id}`);
    return response.data;
  }

  async getPortfolioTransactions(portfolioId: number): Promise<PaginatedResponse<TransactionWithDetails>> {
    const response = await apiClient.get(this.endpoint, { 
      params: { portfolioId } 
    });
    return response.data;
  }
}

export default new TransactionService();
