import { http } from '@/api/http'
import type {
  ImportTemplate,
  ImportJob,
  ImportPreview,
  ImportConfiguration,
  ImportStatistics,
  DataMatcher,
  MatchResult,
  ImportProgress,
  FileUploadResponse,
  ImportReport,
  ImportFilters
} from '@/types/dataImport'

export const dataImportApi = {
  // 获取导入模板列表
  async getImportTemplates(): Promise<ImportTemplate[]> {
    const response = await http.get<ImportTemplate[]>('/import/templates')
    return response.data
  },

  // 获取导入模板详情
  async getImportTemplate(id: string): Promise<ImportTemplate> {
    const response = await http.get<ImportTemplate>(`/import/templates/${id}`)
    return response.data
  },

  // 创建导入模板
  async createImportTemplate(
    template: Omit<ImportTemplate, 'id' | 'createdAt' | 'updatedAt'>
  ): Promise<ImportTemplate> {
    const response = await http.post<ImportTemplate>(
      '/import/templates',
      template
    )
    return response.data
  },

  // 更新导入模板
  async updateImportTemplate(
    id: string,
    template: Partial<ImportTemplate>
  ): Promise<ImportTemplate> {
    const response = await http.put<ImportTemplate>(
      `/import/templates/${id}`,
      template
    )
    return response.data
  },

  // 删除导入模板
  async deleteImportTemplate(id: string): Promise<void> {
    await http.delete(`/import/templates/${id}`)
  },

  // 下载导入模板文件
  async downloadTemplate(
    templateId: string,
    format: 'xlsx' | 'csv' = 'xlsx'
  ): Promise<Blob> {
    const response = await http.get(
      `/import/templates/${templateId}/download`,
      {
        params: { format },
        responseType: 'blob'
      }
    )
    return response.data
  },

  // 上传文件并预览
  async uploadFile(
    file: File,
    templateId?: string
  ): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (templateId) {
      formData.append('template_id', templateId)
    }

    const response = await http.post<FileUploadResponse>(
      '/import/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data
  },

  // 获取文件预览
  async getFilePreview(
    fileId: string,
    sheetName?: string
  ): Promise<ImportPreview> {
    const response = await http.get<ImportPreview>(
      `/import/files/${fileId}/preview`,
      {
        params: { sheet: sheetName }
      }
    )
    return response.data
  },

  // 验证导入数据
  async validateImportData(
    fileId: string,
    configuration: ImportConfiguration
  ): Promise<ImportPreview> {
    const response = await http.post<ImportPreview>(
      `/import/files/${fileId}/validate`,
      configuration
    )
    return response.data
  },

  // 开始导入作业
  async startImportJob(
    fileId: string,
    configuration: ImportConfiguration
  ): Promise<ImportJob> {
    const response = await http.post<ImportJob>('/import/jobs', {
      file_id: fileId,
      ...configuration
    })
    return response.data
  },

  // 获取导入作业列表
  async getImportJobs(
    page: number = 1,
    pageSize: number = 20,
    filters?: ImportFilters
  ): Promise<{
    data: ImportJob[]
    total: number
    page: number
    pageSize: number
  }> {
    const response = await http.get('/import/jobs', {
      params: { page, page_size: pageSize, ...filters }
    })
    return response.data
  },

  // 获取导入作业详情
  async getImportJob(jobId: string): Promise<ImportJob> {
    const response = await http.get<ImportJob>(`/import/jobs/${jobId}`)
    return response.data
  },

  // 取消导入作业
  async cancelImportJob(jobId: string): Promise<ImportJob> {
    const response = await http.post<ImportJob>(`/import/jobs/${jobId}/cancel`)
    return response.data
  },

  // 重试导入作业
  async retryImportJob(jobId: string): Promise<ImportJob> {
    const response = await http.post<ImportJob>(`/import/jobs/${jobId}/retry`)
    return response.data
  },

  // 获取导入进度
  async getImportProgress(jobId: string): Promise<ImportProgress> {
    const response = await http.get<ImportProgress>(
      `/import/jobs/${jobId}/progress`
    )
    return response.data
  },

  // 获取导入报告
  async getImportReport(jobId: string): Promise<ImportReport> {
    const response = await http.get<ImportReport>(
      `/import/jobs/${jobId}/report`
    )
    return response.data
  },

  // 下载导入报告
  async downloadImportReport(
    jobId: string,
    format: 'xlsx' | 'pdf' = 'xlsx'
  ): Promise<Blob> {
    const response = await http.get(`/import/jobs/${jobId}/report/download`, {
      params: { format },
      responseType: 'blob'
    })
    return response.data
  },

  // 获取导入统计
  async getImportStatistics(
    dateRange?: [Date, Date]
  ): Promise<ImportStatistics> {
    const params = dateRange
      ? {
          start_date: dateRange[0].toISOString().split('T')[0],
          end_date: dateRange[1].toISOString().split('T')[0]
        }
      : {}

    const response = await http.get<ImportStatistics>('/import/statistics', {
      params
    })
    return response.data
  },

  // 获取数据匹配器列表
  async getDataMatchers(): Promise<DataMatcher[]> {
    const response = await http.get<DataMatcher[]>('/import/matchers')
    return response.data
  },

  // 创建数据匹配器
  async createDataMatcher(
    matcher: Omit<DataMatcher, 'id'>
  ): Promise<DataMatcher> {
    const response = await http.post<DataMatcher>('/import/matchers', matcher)
    return response.data
  },

  // 更新数据匹配器
  async updateDataMatcher(
    id: string,
    matcher: Partial<DataMatcher>
  ): Promise<DataMatcher> {
    const response = await http.put<DataMatcher>(
      `/import/matchers/${id}`,
      matcher
    )
    return response.data
  },

  // 删除数据匹配器
  async deleteDataMatcher(id: string): Promise<void> {
    await http.delete(`/import/matchers/${id}`)
  },

  // 执行数据匹配
  async matchData(fileId: string, matcherId: string): Promise<MatchResult[]> {
    const response = await http.post<MatchResult[]>('/import/match', {
      file_id: fileId,
      matcher_id: matcherId
    })
    return response.data
  },

  // 确认匹配结果
  async confirmMatches(matchResults: MatchResult[]): Promise<{
    accepted: number
    rejected: number
    manual: number
  }> {
    const response = await http.post('/import/match/confirm', {
      results: matchResults
    })
    return response.data
  },

  // 获取导入历史
  async getImportHistory(
    entityType: string,
    entityId: number
  ): Promise<ImportJob[]> {
    const response = await http.get<ImportJob[]>('/import/history', {
      params: {
        entity_type: entityType,
        entity_id: entityId
      }
    })
    return response.data
  },

  // 清理临时文件
  async cleanupTempFiles(olderThan?: string): Promise<{
    deleted: number
    freed_space: number
  }> {
    const response = await http.post('/import/cleanup', {
      older_than: olderThan
    })
    return response.data
  },

  // 获取支持的文件格式
  async getSupportedFormats(): Promise<{
    formats: string[]
    maxSize: number
    description: Record<string, string>
  }> {
    const response = await http.get('/import/formats')
    return response.data
  },

  // 验证字段映射
  async validateFieldMapping(
    templateId: string,
    mappings: any
  ): Promise<{
    valid: boolean
    errors: string[]
    warnings: string[]
  }> {
    const response = await http.post('/import/validate-mapping', {
      template_id: templateId,
      mappings
    })
    return response.data
  },

  // 获取字段建议
  async getFieldSuggestions(
    templateId: string,
    sourceFields: string[]
  ): Promise<
    {
      field: string
      suggestions: {
        target: string
        confidence: number
        reason: string
      }[]
    }[]
  > {
    const response = await http.post('/import/field-suggestions', {
      template_id: templateId,
      source_fields: sourceFields
    })
    return response.data
  },

  // 执行数据转换测试
  async testDataTransformation(
    templateId: string,
    sampleData: any[],
    mappings: any
  ): Promise<{
    success: boolean
    transformed: any[]
    errors: string[]
  }> {
    const response = await http.post('/import/test-transform', {
      template_id: templateId,
      sample_data: sampleData,
      mappings
    })
    return response.data
  }
}
