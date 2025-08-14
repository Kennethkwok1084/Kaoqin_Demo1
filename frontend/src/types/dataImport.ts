// 数据导入相关类型定义

export interface ImportTemplate {
  id: string
  name: string
  description: string
  type:
    | 'repair_tasks'
    | 'monitoring_tasks'
    | 'assistance_tasks'
    | 'members'
    | 'attendance'
    | 'work_hours'
  requiredFields: string[]
  optionalFields: string[]
  sampleData: Record<string, any>[]
  validationRules: ValidationRule[]
  createdAt: string
  updatedAt: string
}

export interface ValidationRule {
  field: string
  type: 'required' | 'format' | 'range' | 'enum' | 'unique' | 'reference'
  params?: any
  message: string
}

export interface ImportJob {
  id: string
  fileName: string
  fileSize: number
  fileType: string
  templateId: string
  templateName: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  totalRows: number
  successRows: number
  failedRows: number
  validationErrors: ValidationError[]
  processingErrors: ProcessingError[]
  startTime?: string
  endTime?: string
  createdBy: string
  createdAt: string
}

export interface ValidationError {
  row: number
  field: string
  value: any
  error: string
  severity: 'error' | 'warning'
}

export interface ProcessingError {
  row: number
  data: Record<string, any>
  error: string
  errorCode: string
}

export interface ImportPreview {
  headers: string[]
  rows: any[][]
  totalRows: number
  fieldMapping: FieldMapping[]
  validationResults: ValidationResult[]
}

export interface FieldMapping {
  sourceField: string
  targetField: string
  isRequired: boolean
  dataType: 'string' | 'number' | 'date' | 'boolean' | 'enum'
  transformer?: string
  defaultValue?: any
}

export interface ValidationResult {
  field: string
  totalCount: number
  validCount: number
  invalidCount: number
  errors: ValidationError[]
  warnings: ValidationError[]
}

export interface ImportConfiguration {
  templateId: string
  fieldMappings: FieldMapping[]
  options: ImportOptions
}

export interface ImportOptions {
  skipHeader: boolean
  batchSize: number
  continueOnError: boolean
  duplicateHandling: 'skip' | 'update' | 'error'
  dateFormat: string
  encoding: string
  delimiter?: string
}

export interface ImportStatistics {
  totalImports: number
  successfulImports: number
  failedImports: number
  totalRowsProcessed: number
  averageProcessingTime: number
  recentJobs: ImportJob[]
  topErrors: {
    error: string
    count: number
  }[]
}

export interface DataMatcher {
  id: string
  name: string
  description: string
  sourceTable: string
  targetTable: string
  matchingRules: MatchingRule[]
  confidenceThreshold: number
  autoApprove: boolean
}

export interface MatchingRule {
  sourceField: string
  targetField: string
  weight: number
  matchType: 'exact' | 'fuzzy' | 'regex' | 'date_range' | 'numeric_range'
  params?: any
}

export interface MatchResult {
  sourceRow: any
  targetRows: MatchCandidate[]
  bestMatch?: MatchCandidate
  confidence: number
  status: 'matched' | 'multiple' | 'none' | 'manual'
}

export interface MatchCandidate {
  data: any
  confidence: number
  matchDetails: {
    field: string
    sourceValue: any
    targetValue: any
    score: number
  }[]
}

export interface ImportProgress {
  jobId: string
  status: string
  progress: number
  currentStep: string
  processedRows: number
  totalRows: number
  errors: number
  warnings: number
  estimatedTimeRemaining?: number
}

export interface ExcelSheet {
  name: string
  headers: string[]
  rowCount: number
  preview: any[][]
}

export interface FileUploadResponse {
  fileId: string
  fileName: string
  fileSize: number
  sheets?: ExcelSheet[]
  preview: ImportPreview
}

export interface ImportReport {
  jobId: string
  summary: {
    totalRows: number
    successRows: number
    failedRows: number
    warningRows: number
    processingTime: number
  }
  statistics: {
    byField: Record<
      string,
      {
        valid: number
        invalid: number
        warnings: number
      }
    >
    byErrorType: Record<string, number>
  }
  errors: ValidationError[]
  warnings: ValidationError[]
  createdRecords: any[]
  updatedRecords: any[]
  skippedRecords: any[]
}

export interface ImportFilters {
  status?: string
  templateType?: string
  dateRange?: [Date, Date]
  createdBy?: string
}
