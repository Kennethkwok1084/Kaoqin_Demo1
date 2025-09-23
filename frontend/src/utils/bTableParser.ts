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

  const debug = true
  if (debug) {
    console.debug('[BTableParser] 开始解析B表，行数:', worksheet.length)
  }

  const normalizePhoneValue = (value: any): string => {
    if (value === null || value === undefined) {
      return ''
    }
    let digits = value.toString().replace(/\D+/g, '').trim()
    if (!digits) {
      return ''
    }
    if (digits.length > 11) {
      if (digits.startsWith('86')) {
        digits = digits.slice(-11)
      } else if (digits.startsWith('0086')) {
        digits = digits.slice(-11)
      } else {
        digits = digits.slice(-11)
      }
    }
    return digits
  }

  const isMemberStyleTable = () => {
    if (!worksheet || worksheet.length === 0) {
      return false
    }

    const header = worksheet[0] || []
    if (!Array.isArray(header)) {
      return false
    }

    const hasName = header.some(cell => typeof cell === 'string' && cell.includes('姓名'))
    const hasContact = header.some(cell => typeof cell === 'string' && (cell.includes('联系方式') || cell.includes('手机号') || cell.toLowerCase().includes('phone') || cell.includes('联系电话')))

    return hasName && hasContact
  }

  const containsKeyword = (row: any[], keywords: string[]) =>
    Array.isArray(row) && row.some(cell => typeof cell === 'string' && keywords.some(keyword => cell.includes(keyword)))

  const isRowEmpty = (row: any[]) => !Array.isArray(row) || row.every(cell => cell === undefined || cell === null || cell === '')

  const parseMemberStyleTable = () => {
    const header = worksheet[0] || []

    const findIndex = (keywords: string[]) =>
      header.findIndex(cell => typeof cell === 'string' && keywords.some(keyword => cell.includes(keyword)))

    const nameIndex = findIndex(['姓名'])
    const contactIndex = findIndex(['联系方式', '联系电话', '手机号', '电话', '手机', 'contact', 'phone'])
    const locationIndex = findIndex(['部门', '单位', '院系', '位置', '地点', '班级'])

    if (nameIndex === -1 || contactIndex === -1) {
      if (debug) {
        console.debug('[BTableParser] 成员样式表缺少姓名或联系方式列')
      }
      return
    }

    for (let i = 1; i < worksheet.length; i += 1) {
      const row = worksheet[i]
      if (!Array.isArray(row)) {
        continue
      }

      const reporterName = extractCellValue(row[nameIndex]).trim()
      const contact = normalizePhoneValue(extractCellValue(row[contactIndex]))

      if (!reporterName && !contact) {
        continue
      }

      const record: BTableRecord = {
        reporterName,
        location: locationIndex !== -1 ? extractCellValue(row[locationIndex]) : '',
        contact,
        inspector: '',
        result: '',
        repairType: '',
        repairContent: '',
        inspectContent: ''
      }

      result.data.push(record)
      result.validRows += 1

      if (debug) {
        console.debug('[BTableParser] 成员样式记录:', record)
      }
    }
  }

  try {
    if (isMemberStyleTable()) {
      if (debug) {
        console.debug('[BTableParser] 检测到成员列表样式B表')
      }
      parseMemberStyleTable()
      result.success = result.validRows > 0

      if (debug) {
        console.debug('[BTableParser] 成员样式解析完成，有效记录数:', result.validRows)
      }

      return result
    }

    // 跳过标题行，从第3行开始（索引2）
    let i = 2

    while (i < worksheet.length) {
      const row1 = worksheet[i] || []
      const row2 = worksheet[i + 1] || []

      if (debug) {
        console.debug(`[BTableParser] 检查第${i + 1}行和第${i + 2}行`, row1, row2)
      }

      // 跳过空行
      if (isRowEmpty(row1) && isRowEmpty(row2)) {
        if (debug) {
          console.debug(`[BTableParser] 第${i + 1}行为空，跳过`)
        }
        i += 1
        continue
      }

      // 检查是否为有效的数据行
      // 第一行第一列应该包含"报修日期"或者第三列有实际数据
      const isDataRow = (
        (row1[0] && row1[0].toString().includes('报修日期')) ||
        (row1[3] && row1[3].toString().trim() && !row1[3].toString().includes('报修人姓名'))
      )

      if (isDataRow) {
        if (debug) {
          console.debug(`[BTableParser] 识别到有效数据段，起始行号: ${i + 1}`)
        }
        try {
          // 提取基本信息（第一行）
          const reporterName = extractCellValue(row1[3]) // 列D: 报修人姓名
          const location = extractCellValue(row1[5]) // 列F: 报修地点
          const contact = normalizePhoneValue(extractCellValue(row1[7])) // 列H: 联系方式
          const inspector = extractCellValue(row1[9]) // 列J: 检修人
          const inspectResult = extractCellValue(row1[11]) // 列L: 检修结果
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
            result: inspectResult || '',
            repairType: repairType || '',
            repairContent: repairContent || '',
            inspectContent: inspectContent || ''
          }

          result.data.push(record)
          result.validRows++

          if (debug) {
            console.debug('[BTableParser] 解析得到记录:', record)
          }

        } catch (error) {
          const errorMsg = `第${i + 1}行解析失败: ${error}`
          result.errors.push(errorMsg)
          console.warn(errorMsg)
        }
      }

      if (isDataRow) {
        // 移动到下一组数据（跳过3行）
        i += 3
      } else {
        // 非有效数据段，逐行前进，避免跳过真正的数据
        if (
          containsKeyword(row1, ['报修信息', '检修信息']) ||
          containsKeyword(row1, ['时间：', '时间:'])
        ) {
          i += 1
        } else {
          i += 1
        }
      }
    }

    result.success = result.errors.length === 0 || result.validRows > 0

    if (debug) {
      console.debug('[BTableParser] 解析完成，有效记录数:', result.validRows, '错误数:', result.errors.length)
    }

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
  const previewRows = worksheet.slice(0, 10)

  const containsKeyword = (rows: any[][], keyword: string) =>
    rows.some(row =>
      Array.isArray(row) && row.some(cell => typeof cell === 'string' && cell.includes(keyword))
    )

  const hasTimeRow = containsKeyword(previewRows, '时间')
  const hasRepairHeader = containsKeyword(previewRows, '报修信息')
  const hasInspectHeader = containsKeyword(previewRows, '检修信息')
  const hasRepairDate = containsKeyword(previewRows, '报修日期')

  if (hasRepairHeader && hasInspectHeader && hasRepairDate) {
    return { isValid: true }
  }

  if (hasTimeRow && hasRepairDate) {
    return { isValid: true }
  }

  // 成员表样式：第一行包含姓名和联系方式/手机号
  const header = worksheet[0] || []
  if (
    Array.isArray(header) &&
    header.some(cell => typeof cell === 'string' && cell.includes('姓名')) &&
    header.some(cell => typeof cell === 'string' && (cell.includes('联系方式') || cell.includes('联系电话') || cell.includes('手机号') || cell.includes('电话') || cell.toLowerCase().includes('phone')))
  ) {
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
