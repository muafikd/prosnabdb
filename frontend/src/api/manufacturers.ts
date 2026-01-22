import apiClient from './axios'
import type { AxiosResponse } from 'axios'

// Manufacturer Types
export interface Manufacturer {
    manufacturer_id: number
    manufacturer_name: string
    manufacturer_country?: string
    manufacturer_website?: string
    manufacturer_description?: string
    created_at: string
    updated_at: string
}

export interface ManufacturerCreateData {
    manufacturer_name: string
    manufacturer_country?: string
    manufacturer_website?: string
    manufacturer_description?: string
}

export interface ManufacturerUpdateData extends Partial<ManufacturerCreateData> { }

export interface ManufacturersListResponse {
    count?: number
    next?: string | null
    previous?: string | null
    results?: Manufacturer[]
}

export type ManufacturersResponse = ManufacturersListResponse | Manufacturer[]

// API functions
export const manufacturersAPI = {
    // Get list of manufacturers
    async getManufacturers(params?: { search?: string; page?: number }): Promise<ManufacturersResponse> {
        const response: AxiosResponse<ManufacturersResponse> = await apiClient.get('/manufacturers/', { params })
        return response.data
    },

    // Get manufacturer by ID
    async getManufacturer(id: number): Promise<Manufacturer> {
        const response: AxiosResponse<Manufacturer> = await apiClient.get(`/manufacturers/${id}/`)
        return response.data
    },

    // Create manufacturer
    async createManufacturer(data: ManufacturerCreateData): Promise<Manufacturer> {
        const response: AxiosResponse<Manufacturer> = await apiClient.post('/manufacturers/', data)
        return response.data
    },

    // Update manufacturer
    async updateManufacturer(id: number, data: ManufacturerUpdateData): Promise<Manufacturer> {
        const response: AxiosResponse<Manufacturer> = await apiClient.patch(`/manufacturers/${id}/`, data)
        return response.data
    },

    // Delete manufacturer
    async deleteManufacturer(id: number): Promise<void> {
        await apiClient.delete(`/manufacturers/${id}/`)
    },
}
