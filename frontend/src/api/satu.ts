import apiClient from './axios'
import type { AxiosResponse } from 'axios'

export interface SatuCheckResponse {
    ok: boolean
    result?: unknown
    error?: string
}

export interface SatuExportResponse {
    ok: boolean
    result?: unknown
    error?: string
    success_count?: number
    errors?: string[]
}

export const satuAPI = {
    async checkConnection(satu_api_token?: string): Promise<SatuCheckResponse> {
        const response: AxiosResponse<SatuCheckResponse> = await apiClient.post('/satu/check/', {
            satu_api_token: satu_api_token || undefined,
        })
        return response.data
    },

    async exportEquipment(equipmentId: number): Promise<SatuExportResponse> {
        const response: AxiosResponse<SatuExportResponse> = await apiClient.post(`/satu/equipment/${equipmentId}/export/`)
        return response.data
    },

    async exportBulkEquipment(): Promise<SatuExportResponse> {
        const response: AxiosResponse<SatuExportResponse> = await apiClient.post('/satu/equipment/export-bulk/')
        return response.data
    }
}
