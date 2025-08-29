// 完美的通用类型定义系统
export interface ApiResponse<T = any> {
  data: T
  message: string
  success: boolean
  code?: number
}

export interface PaginationParams {
  page: number
  page_size: number
  search?: string
  [key: string]: any
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface BaseEntity {
  id: number
  created_at: string
  updated_at: string
}

export interface FilterableEntity {
  [key: string]: any
}

export interface SortableParams {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface TimeRange {
  start_date?: string
  end_date?: string
}

export interface BaseError {
  message: string
  code?: string | number
  details?: any
}

export interface AsyncState<T = any> {
  data: T | null
  loading: boolean
  error: BaseError | null
}

export interface StoreState<T = any> extends AsyncState<T> {
  initialized: boolean
  lastUpdated: string | null
}

export type RequestStatus = 'idle' | 'loading' | 'success' | 'error'

export interface RequestState {
  status: RequestStatus
  error: BaseError | null
}