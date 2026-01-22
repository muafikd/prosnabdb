export const formatPrice = (value: number | string | undefined | null, currency: string = ''): string => {
    if (value === undefined || value === null || value === '') return '-'
    const num = typeof value === 'string' ? parseFloat(value) : value
    if (isNaN(num)) return '-'

    // Format: 15 000.00
    // toFixed(2) gives "15000.00"
    // split('.') gives ["15000", "00"]
    // replace regex adds spaces to the first part
    const parts = num.toFixed(2).split('.')
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
    const formatted = parts.join('.')

    return currency ? `${formatted} ${currency}` : formatted
}

export const inputFormatter = (value: number | string): string => {
    return `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export const inputParser = (value: string): string => {
    return value.replace(/\s/g, '')
}
