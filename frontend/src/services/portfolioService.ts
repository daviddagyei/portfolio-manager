import apiClient from './apiClient';
import { 
  Portfolio, 
  PortfolioCreate, 
  PortfolioUpdate, 
  PortfolioSummary,
  PortfolioSearchParams,
  ApiResponse,
  PaginatedResponse
} from '../types';

class PortfolioService {
  private endpoint = '/portfolios';

  async getPortfolios(params?: PortfolioSearchParams): Promise<PaginatedResponse<Portfolio>> {
    const response = await apiClient.get(this.endpoint, { params });
    return response.data;
  }

  async getPortfolio(id: number): Promise<ApiResponse<Portfolio>> {
    const response = await apiClient.get(`${this.endpoint}/${id}`);
    return response.data;
  }

  async createPortfolio(portfolio: PortfolioCreate): Promise<ApiResponse<Portfolio>> {
    const response = await apiClient.post(this.endpoint, portfolio);
    return response.data;
  }

  async updatePortfolio(id: number, portfolio: PortfolioUpdate): Promise<ApiResponse<Portfolio>> {
    const response = await apiClient.put(`${this.endpoint}/${id}`, portfolio);
    return response.data;
  }

  async deletePortfolio(id: number): Promise<ApiResponse<void>> {
    const response = await apiClient.delete(`${this.endpoint}/${id}`);
    return response.data;
  }

  async getPortfolioSummary(id: number): Promise<ApiResponse<PortfolioSummary>> {
    const response = await apiClient.get(`${this.endpoint}/${id}/summary`);
    return response.data;
  }

  async getUserPortfolios(userId: number): Promise<PaginatedResponse<Portfolio>> {
    const response = await apiClient.get(this.endpoint, { 
      params: { userId } 
    });
    return response.data;
  }

  async getPortfolioHoldings(id: number): Promise<ApiResponse<any[]>> {
    const response = await apiClient.get(`${this.endpoint}/${id}/holdings`);
    return response.data;
  }

  async updatePortfolioHolding(portfolioId: number, assetId: number, data: any): Promise<ApiResponse<any>> {
    const response = await apiClient.put(`${this.endpoint}/${portfolioId}/holdings/${assetId}`, data);
    return response.data;
  }

  async deletePortfolioHolding(portfolioId: number, holdingId: number): Promise<ApiResponse<void>> {
    const response = await apiClient.delete(`${this.endpoint}/${portfolioId}/holdings/${holdingId}`);
    return response.data;
  }
}

const portfolioService = new PortfolioService();
export default portfolioService;
