import apiClient from './axios'
import type { AxiosResponse } from 'axios'

// Типы для оборудования
export interface EquipmentDetail {
  detail_id: number
  detail_parameter_name: string
  detail_parameter_value?: string
}

export interface EquipmentSpecification {
  spec_id: number
  spec_parameter_name: string
  spec_parameter_value?: string
}

export interface EquipmentTechProcess {
  tech_id: number
  tech_name: string
  tech_value?: string
  tech_desc?: string
}

export interface Equipment {
  equipment_id: number
  equipment_name: string
  equipment_articule?: string
  equipment_uom?: string
  equipment_short_description?: string
  equipment_warranty?: string
  is_published: boolean
  categories: number[]
  manufacturers: number[]
  equipment_types: number[]
  details: EquipmentDetail[]
  specifications: EquipmentSpecification[]
  tech_processes: EquipmentTechProcess[]
  equipment_imagelinks?: string
  equipment_videolinks?: string
  equipment_manufacture_price?: string
  equipment_madein_country?: string
  equipment_price_currency_type?: string
  created_at: string
  updated_at: string
}

export interface EquipmentCreateData {
  equipment_name: string
  equipment_articule?: string
  equipment_uom?: string
  equipment_short_description?: string
  equipment_warranty?: string
  is_published?: boolean
  categories?: number[]
  manufacturers?: number[]
  equipment_types?: number[]
  equipment_imagelinks?: string
  equipment_videolinks?: string
  equipment_manufacture_price?: string
  equipment_madein_country?: string
  equipment_price_currency_type?: string
}

export interface EquipmentUpdateData extends Partial<EquipmentCreateData> {}

export type EquipmentResponse = Equipment[] | { count: number; next: string | null; previous: string | null; results: Equipment[] }

// Типы для связанных моделей
export interface Category {
  category_id: number
  category_name: string
  category_description?: string
}

export interface Manufacturer {
  manufacturer_id: number
  manufacturer_name: string
  manufacturer_country?: string
}

export interface EquipmentType {
  type_id: number
  type_name: string
}

// API функции для работы с оборудованием
export const equipmentAPI = {
  // Получить список оборудования
  async getEquipment(params?: { search?: string; category?: number; manufacturer?: number; is_published?: boolean; page?: number }): Promise<EquipmentResponse> {
    const response: AxiosResponse<EquipmentResponse> = await apiClient.get('/equipment/', { params })
    return response.data
  },

  // Получить оборудование по ID
  async getEquipmentById(equipmentId: number): Promise<Equipment> {
    const response: AxiosResponse<Equipment> = await apiClient.get(`/equipment/${equipmentId}/`)
    return response.data
  },

  // Создать оборудование
  async createEquipment(data: EquipmentCreateData): Promise<Equipment> {
    const response: AxiosResponse<Equipment> = await apiClient.post('/equipment/', data)
    return response.data
  },

  // Обновить оборудование
  async updateEquipment(equipmentId: number, data: EquipmentUpdateData): Promise<Equipment> {
    const response: AxiosResponse<Equipment> = await apiClient.patch(`/equipment/${equipmentId}/`, data)
    return response.data
  },

  // Удалить оборудование
  async deleteEquipment(equipmentId: number): Promise<void> {
    await apiClient.delete(`/equipment/${equipmentId}/`)
  },
}

// API функции для связанных моделей
export interface CategoryCreateData {
  category_name: string
  category_description?: string
}

export interface ManufacturerCreateData {
  manufacturer_name: string
  manufacturer_country?: string
}

export interface EquipmentTypeCreateData {
  type_name: string
}

export const categoriesAPI = {
  async getCategories(): Promise<Category[]> {
    const response: AxiosResponse<Category[]> = await apiClient.get('/categories/')
    return Array.isArray(response.data) ? response.data : (response.data as any).results || []
  },
  async createCategory(data: CategoryCreateData): Promise<Category> {
    const response: AxiosResponse<Category> = await apiClient.post('/categories/', data)
    return response.data
  },
  async deleteCategory(categoryId: number): Promise<void> {
    await apiClient.delete(`/categories/${categoryId}/`)
  },
}

export const manufacturersAPI = {
  async getManufacturers(): Promise<Manufacturer[]> {
    const response: AxiosResponse<Manufacturer[]> = await apiClient.get('/manufacturers/')
    return Array.isArray(response.data) ? response.data : (response.data as any).results || []
  },
  async createManufacturer(data: ManufacturerCreateData): Promise<Manufacturer> {
    const response: AxiosResponse<Manufacturer> = await apiClient.post('/manufacturers/', data)
    return response.data
  },
  async deleteManufacturer(manufacturerId: number): Promise<void> {
    await apiClient.delete(`/manufacturers/${manufacturerId}/`)
  },
}

export const equipmentTypesAPI = {
  async getEquipmentTypes(): Promise<EquipmentType[]> {
    const response: AxiosResponse<EquipmentType[]> = await apiClient.get('/equipment-types/')
    return Array.isArray(response.data) ? response.data : (response.data as any).results || []
  },
  async createEquipmentType(data: EquipmentTypeCreateData): Promise<EquipmentType> {
    const response: AxiosResponse<EquipmentType> = await apiClient.post('/equipment-types/', data)
    return response.data
  },
  async deleteEquipmentType(typeId: number): Promise<void> {
    await apiClient.delete(`/equipment-types/${typeId}/`)
  },
}

// API функции для деталей, спецификаций и техпроцессов
export interface EquipmentDetailCreateData {
  equipment?: number
  detail_parameter_name: string
  detail_parameter_value?: string
}

export interface EquipmentSpecificationCreateData {
  equipment?: number
  spec_parameter_name: string
  spec_parameter_value?: string
}

export interface EquipmentTechProcessCreateData {
  equipment?: number
  tech_name: string
  tech_value?: string
  tech_desc?: string
}

export const equipmentDetailsAPI = {
  async createDetail(data: EquipmentDetailCreateData): Promise<EquipmentDetail> {
    const response: AxiosResponse<EquipmentDetail> = await apiClient.post('/equipment-details/', data)
    return response.data
  },
  async updateDetail(detailId: number, data: Partial<EquipmentDetailCreateData>): Promise<EquipmentDetail> {
    const response: AxiosResponse<EquipmentDetail> = await apiClient.patch(`/equipment-details/${detailId}/`, data)
    return response.data
  },
  async deleteDetail(detailId: number): Promise<void> {
    await apiClient.delete(`/equipment-details/${detailId}/`)
  },
}

export const equipmentSpecificationsAPI = {
  async createSpecification(data: EquipmentSpecificationCreateData): Promise<EquipmentSpecification> {
    const response: AxiosResponse<EquipmentSpecification> = await apiClient.post('/equipment-specifications/', data)
    return response.data
  },
  async updateSpecification(specId: number, data: Partial<EquipmentSpecificationCreateData>): Promise<EquipmentSpecification> {
    const response: AxiosResponse<EquipmentSpecification> = await apiClient.patch(`/equipment-specifications/${specId}/`, data)
    return response.data
  },
  async deleteSpecification(specId: number): Promise<void> {
    await apiClient.delete(`/equipment-specifications/${specId}/`)
  },
}

export const equipmentTechProcessesAPI = {
  async createTechProcess(data: EquipmentTechProcessCreateData): Promise<EquipmentTechProcess> {
    const response: AxiosResponse<EquipmentTechProcess> = await apiClient.post('/equipment-tech-processes/', data)
    return response.data
  },
  async updateTechProcess(techId: number, data: Partial<EquipmentTechProcessCreateData>): Promise<EquipmentTechProcess> {
    const response: AxiosResponse<EquipmentTechProcess> = await apiClient.patch(`/equipment-tech-processes/${techId}/`, data)
    return response.data
  },
  async deleteTechProcess(techId: number): Promise<void> {
    await apiClient.delete(`/equipment-tech-processes/${techId}/`)
  },
}

// API функции для логистики
export interface Logistics {
  logistics_id: number
  equipment: number
  route_type: 'china_kz' | 'russia_kz' | 'kz_warehouse' | 'other'
  cost: string
  currency: string
  estimated_days?: number
  is_active: boolean
  notes?: string
  created_at: string
  updated_at: string
}

export interface LogisticsCreateData {
  equipment: number
  route_type: 'china_kz' | 'russia_kz' | 'kz_warehouse' | 'other'
  cost: string
  currency: string
  estimated_days?: number
  is_active?: boolean
  notes?: string
}

export interface LogisticsUpdateData extends Partial<LogisticsCreateData> {}

export const logisticsAPI = {
  // Получить логистику по оборудованию
  async getLogisticsByEquipment(equipmentId: number): Promise<Logistics[]> {
    const response: AxiosResponse<Logistics[]> = await apiClient.get('/logistics/', { params: { equipment: equipmentId } })
    return Array.isArray(response.data) ? response.data : (response.data as any).results || []
  },

  // Создать логистику
  async createLogistics(data: LogisticsCreateData): Promise<Logistics> {
    const response: AxiosResponse<Logistics> = await apiClient.post('/logistics/', data)
    return response.data
  },

  // Обновить логистику
  async updateLogistics(logisticsId: number, data: LogisticsUpdateData): Promise<Logistics> {
    const response: AxiosResponse<Logistics> = await apiClient.patch(`/logistics/${logisticsId}/`, data)
    return response.data
  },

  // Удалить логистику
  async deleteLogistics(logisticsId: number): Promise<void> {
    await apiClient.delete(`/logistics/${logisticsId}/`)
  },
}

