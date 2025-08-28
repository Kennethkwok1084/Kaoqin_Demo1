/**
 * 全局类型声明
 * 按照"如无必要勿增加实体"原则，只添加必要的类型声明
 */

declare namespace NodeJS {
  interface Timeout {}
}

// Element Plus 类型断言辅助
declare global {
  type ElementPlusType = 'success' | 'warning' | 'info' | 'primary' | 'danger'
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  type EpPropMergeType<T, K, V> = any
  type TabPaneName = string | number
  type ModelValueType = string | number | Date | string[] | [any, any]
  type DateModelType = string | Date
}

export {}
