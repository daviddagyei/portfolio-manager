import apiClient from './apiClient';
import { 
  Asset, 
  AssetCreate, 
  AssetUpdate, 
  AssetSearchParams,
  ApiResponse,
  PaginatedResponse
} from '../types';

class AssetService {
  private endpoint = '/assets';

  async getAssets(params?: AssetSearchParams): Promise<PaginatedResponse<Asset>> {
    const response = await apiClient.get(this.endpoint, { params });
    return response.data;
  }

  async getAsset(id: number): Promise<ApiResponse<Asset>> {
    const response = await apiClient.get(`${this.endpoint}/${id}`);
    return response.data;
  }

  async createAsset(asset: AssetCreate): Promise<ApiResponse<Asset>> {
    const response = await apiClient.post(this.endpoint, asset);
    return response.data;
  }

  async updateAsset(id: number, asset: AssetUpdate): Promise<ApiResponse<Asset>> {
    const response = await apiClient.put(`${this.endpoint}/${id}`, asset);
    return response.data;
  }

  async deleteAsset(id: number): Promise<ApiResponse<void>> {
    const response = await apiClient.delete(`${this.endpoint}/${id}`);
    return response.data;
  }

  async searchAssets(query: string): Promise<PaginatedResponse<Asset>> {
    const response = await apiClient.get(`${this.endpoint}`, { 
      params: { search: query } 
    });
    return response.data;
  }
}

const assetService = new AssetService();
export default assetService;
