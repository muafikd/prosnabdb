import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { exchangeRatesAPI, type ExchangeRate } from '@/api/exchangeRates'
import { ElMessage } from 'element-plus'

export const useExchangeRateStore = defineStore('exchangeRate', () => {
    const rates = ref<ExchangeRate[]>([])
    const loading = ref(false)
    const lastUpdated = ref<string | null>(null)

    // Format today's date for display/filtering
    const todayDate = computed(() => {
        return new Date().toISOString().split('T')[0]
    })

    // Fetch latest official rates
    const fetchRates = async () => {
        loading.value = true
        try {
            // Fetch active official rates for today (or latest available if needed)
            // Usually we want today's rates. If empty, maybe show previous?
            // For now, let's fetch active=true
            const fetchedRates = await exchangeRatesAPI.getRates({
                is_active: true,
                is_official: true,
                latest: true // Use our backend feature to get latest unique per pair
            })
            // Deduplicate by currency_from/currency_to; keep first (latest) occurrence
            const seen = new Set<string>()
            const unique: ExchangeRate[] = []
            for (const r of fetchedRates) {
                const key = `${r.currency_from}-${r.currency_to}`
                if (seen.has(key)) continue
                seen.add(key)
                unique.push(r)
            }
            rates.value = unique
            // Определяем время последнего обновления по максимуму updated_at/created_at
            const timestamps = fetchedRates
                .map(r => r.updated_at || r.created_at)
                .filter(Boolean) as string[]
            if (timestamps.length > 0) {
                lastUpdated.value = timestamps.sort().slice(-1)[0]
            } else {
                lastUpdated.value = null
            }
        } catch (error: any) {
            console.error('Failed to fetch exchange rates', error)
            ElMessage.error('Не удалось загрузить курсы валют')
        } finally {
            loading.value = false
        }
    }

    const syncRates = async () => {
        loading.value = true
        try {
            const result = await exchangeRatesAPI.syncRates()
            ElMessage.success(`Синхронизация успешна. Обновлено: ${result.stats.updated}, Создано: ${result.stats.created}`)
            await fetchRates()
        } catch (error: any) {
            console.error('Sync failed', error)
            ElMessage.error(error.response?.data?.error || 'Ошибка синхронизации')
        } finally {
            loading.value = false
        }
    }

    const addCurrency = async (currencyCode: string) => {
        loading.value = true
        try {
            const result = await exchangeRatesAPI.addCurrency(currencyCode)
            ElMessage.success(result.message)
            await fetchRates()
            return true
        } catch (error: any) {
            console.error('Add currency failed', error)
            ElMessage.error(error.response?.data?.error || 'Ошибка добавления валюты')
            return false
        } finally {
            loading.value = false
        }
    }

    const deleteRate = async (rateId: number) => {
        loading.value = true
        try {
            await exchangeRatesAPI.deleteRate(rateId)
            ElMessage.success('Валюта удалена из списка')
            // Remove from local list immediately
            rates.value = rates.value.filter(r => r.rate_id !== rateId)
        } catch (error: any) {
            console.error('Delete rate failed', error)
            ElMessage.error(error.response?.data?.error || 'Ошибка удаления валюты')
        } finally {
            loading.value = false
        }
    }

    // Get rate for specific currency (to KZT)
    const getRate = (currencyFrom: string) => {
        return rates.value.find(r => r.currency_from === currencyFrom && r.currency_to === 'KZT')
    }

    return {
        rates,
        loading,
        todayDate,
        fetchRates,
        syncRates,
        addCurrency,
        deleteRate,
        getRate
        ,
        lastUpdated
    }
})
