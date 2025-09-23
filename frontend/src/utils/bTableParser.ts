/**
 * B表解析工具
 * B表格式：每3行为一组记录
 * 第1行：基本信息（报修人姓名、报修地点、联系方式、检修人、检修结果、检修形式）
 * 第2行：内容信息（报修内容、检修内容）
 * 第3行：空行分隔
 */

export interface BTableRecord {
  reporterName: string // 报修人姓名
  location: string // 报修地点
  contact: string // 联系方式
  inspector: string // 检修人
  result: string // 检修结果
  repairType: string // 检修形式（线上/现场）
  repairContent: string // 报修内容
  inspectContent: string // 检修内容
}

export interface ParsedBTable {
  success: boolean
  data: BTableRecord[]
  errors: string[]
  totalRows: number
  validRows: number
}

/**
 * 解析B表Excel数据
 * @param worksheet Excel工作表数据
 * @returns 解析结果
 */
export function parseBTable(worksheet: any[][]): ParsedBTable {
  const result: ParsedBTable = {
    success: true,
    data: [],
    errors: [],
    totalRows: worksheet.length,
    validRows: 0
  }

  try {
    // 跳过标题行，从第3行开始（索引2）
    let i = 2

    while (i < worksheet.length) {
      const row1 = worksheet[i] || []
      const row2 = worksheet[i + 1] || []

      // 检查是否为有效的数据行
      // 第一行第一列应该包含"报修日期"或者第三列有实际数据
      const isDataRow = (
        (row1[0] && row1[0].toString().includes('报修日期')) ||
        (row1[3] && row1[3].toString().trim() && !row1[3].toString().includes('报修人姓名'))
      )

      if (isDataRow) {
        try {
          // 提取基本信息（第一行）
          const reporterName = extractCellValue(row1[3]) // 列D: 报修人姓名
          const location = extractCellValue(row1[5]) // 列F: 报修地点
          const contact = extractCellValue(row1[7]) // 列H: 联系方式
          const inspector = extractCellValue(row1[9]) // 列J: 检修人
          const result = extractCellValue(row1[11]) // 列L: 检修结果
          const repairType = extractCellValue(row1[13]) // 列N: 检修形式

          // 提取内容信息（第二行）
          const repairContent = extractCellValue(row2[3]) // 列D: 报修内容
          const inspectContent = extractCellValue(row2[9]) // 列J: 检修内容

          // 验证必填字段
          if (!reporterName && !location && !contact) {
            // 如果关键字段都为空，跳过这行
            i += 3
            continue
          }

          const record: BTableRecord = {
            reporterName: reporterName || '',
            location: location || '',
            contact: contact || '',
            inspector: inspector || '',
            result: result || '',
            repairType: repairType || '',
            repairContent: repairContent || '',
            inspectContent: inspectContent || ''
          }

          result.data.push(record)
          result.validRows++

        } catch (error) {
          const errorMsg = `第${i + 1}行解析失败: ${error}`
          result.errors.push(errorMsg)
          console.warn(errorMsg)
        }
      }

      // 移动到下一组数据（跳过3行）
      i += 3
    }

    result.success = result.errors.length === 0 || result.validRows > 0

  } catch (error) {
    result.success = false
    result.errors.push(`B表解析失败: ${error}`)
    console.error('B表解析错误:', error)
  }

  return result
}

/**
 * 提取单元格值，处理各种数据类型
 */
function extractCellValue(cell: any): string {
  if (cell === null || cell === undefined) {
    return ''
  }

  if (typeof cell === 'number') {
    // 处理科学计数法的电话号码
    if (cell > 1e10) {
      return cell.toString()
    }
    return cell.toString()
  }

  if (typeof cell === 'string') {
    return cell.trim()
  }

  return cell.toString().trim()
}

/**
 * 验证B表格式
 * @param worksheet Excel工作表数据
 * @returns 是否为有效的B表格式
 */
export function validateBTableFormat(worksheet: any[][]): {
  isValid: boolean
  error?: string
} {
  if (!worksheet || worksheet.length < 3) {
    return {
      isValid: false,
      error: 'B表至少需要3行数据'
    }
  }

  // 检查第一行是否包含时间信息
  const firstRow = worksheet[0] || []
  if (firstRow[0] && firstRow[0].toString().includes('时间：')) {
    return { isValid: true }
  }

  // 检查第二行是否包含"报修信息"和"检修信息"标题
  const secondRow = worksheet[1] || []
  const hasRepairInfo = secondRow[0] && secondRow[0].toString().includes('报修信息')
  const hasInspectInfo = secondRow[8] && secondRow[8].toString().includes('检修信息')

  if (hasRepairInfo && hasInspectInfo) {
    return { isValid: true }
  }

  return {
    isValid: false,
    error: 'B表格式不正确，缺少必要的标题行'
  }
}

/**
 * 将B表记录转换为A表格式（用于A-B表匹配）
 * @param bRecords B表记录数组
 * @returns 转换后的A表格式记录
 */
export function convertBTableToAFormat(bRecords: BTableRecord[]): any[] {
  return bRecords.map((record, index) => ({
    id: `B_${index + 1}`,
    reporterName: record.reporterName,
    contact: record.contact,
    location: record.location,
    content: record.repairContent,
    inspector: record.inspector,
    result: record.result,
    repairType: record.repairType,
    inspectContent: record.inspectContent,
    source: 'B表'
  }))
}