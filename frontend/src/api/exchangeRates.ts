import apiClient from './axios'
import type { AxiosResponse } from 'axios'

export interface ExchangeRate {
    rate_id: number
    currency_from: string
    currency_from_display?: string
    currency_to: string
    currency_to_display?: string
    rate_value: string
    rate_date: string
    source: string
    source_display?: string
    is_active: boolean
    is_official: boolean
    created_at?: string
    updated_at?: string
}

export interface ExchangeRateStats {
    created: number
    updated: number
    skipped_manual: number
    errors: number
}

export const exchangeRatesAPI = {
    // Get list of exchange rates (active by default or with filters)
    async getRates(params?: {
        date_from?: string
        date_to?: string
        is_active?: boolean
        is_official?: boolean
        currency_from?: string
        latest?: boolean
    }): Promise<ExchangeRate[]> {
        const response: AxiosResponse<ExchangeRate[]> = await apiClient.get('/exchange-rates/', { params })
        return Array.isArray(response.data) ? response.data : (response.data as any).results || []
    },

    // Trigger manual synchronization
    async syncRates(): Promise<{ message: string; stats: ExchangeRateStats }> {
        const response = await apiClient.post('/exchange-rates/sync/')
        return response.data
    },

    // Add new currency ticker
    async addCurrency(currencyCode: string): Promise<{ message: string; rate: ExchangeRate; created: boolean }> {
        const response = await apiClient.post('/exchange-rates/add/', { currency_code: currencyCode })
        return response.data
    },

    // Delete rate (stop tracking/hide)
    async deleteRate(rateId: number): Promise<void> {
        await apiClient.delete(`/exchange-rates/${rateId}/`)
    },
}
