import apiClient from './apiClient';
import { 
  PriceData, 
  PriceDataCreate, 
  PriceHistoryRequest,
  PriceHistoryResponse,
  MarketDataSearchParams,
  ApiResponse,
  PaginatedResponse
} from '../types';

class MarketDataService {
  private endpoint = '/market-data';

  async getPriceData(params?: MarketDataSearchParams): Promise<PaginatedResponse<PriceData>> {
    const response = await apiClient.get(this.endpoint, { params });
    return response.data;
  }

  async createPriceData(priceData: PriceDataCreate): Promise<ApiResponse<PriceData>> {
    const response = await apiClient.post(this.endpoint, priceData);
    return response.data;
  }

  async getPriceHistory(request: PriceHistoryRequest): Promise<PriceHistoryResponse> {
    const response = await apiClient.post(`${this.endpoint}/history`, request);
    return response.data;
  }

  async getLatestPrice(assetId: number): Promise<ApiResponse<PriceData>> {
    const response = await apiClient.get(`${this.endpoint}/latest/${assetId}`);
    return response.data;
  }

  async refreshPriceData(assetId: number): Promise<ApiResponse<PriceData>> {
    const response = await apiClient.post(`${this.endpoint}/refresh/${assetId}`);
    return response.data;
  }
}

const marketDataService = new MarketDataService();
export default marketDataService;
