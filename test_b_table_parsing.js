/**
 * B表解析功能测试脚本
 * 在浏览器控制台中运行，用于测试B表解析器
 */

// 模拟B表Excel数据结构
const mockBTableData = [
  ['时间：2025.09', null, null, null, null, null, null, null, null, null, null, null, null, null],
  ['报修信息', null, null, null, null, null, null, null, '检修信息', null, null, null, null, null],
  ['报修日期', null, '报修人姓名', '俊坤1', '报修地点', '43号公寓,2层,A202C区', '联系方式', 13398649566, '检修人', '赵一鸣', '检修结果', '正常', '检修形式', '现场'],
  [null, null, '报修内容', '111', null, null, null, null, '检修内容', '测试网络', null, null, null, null],
  [null, null, null, null, null, null, null, null, null, null, null, null, null, null],
  ['报修日期', null, '报修人姓名', '李老师', '报修地点', '教学楼B座501', '联系方式', 13900139000, '检修人', '王工程师', '检修结果', '已完成', '检修形式', '线上'],
  [null, null, '报修内容', '网络连接异常', null, null, null, null, '检修内容', '更新网络配置', null, null, null, null],
  [null, null, null, null, null, null, null, null, null, null, null, null, null, null]
]

// 测试解析函数
async function testBTableParsing() {
  console.log('开始测试B表解析功能...')

  try {
    // 动态导入解析器模块
    const { parseBTable, validateBTableFormat } = await import('./frontend/src/utils/bTableParser.ts')

    // 1. 测试格式验证
    console.log('1. 测试格式验证...')
    const formatValidation = validateBTableFormat(mockBTableData)
    console.log('格式验证结果:', formatValidation)

    if (!formatValidation.isValid) {
      console.error('B表格式验证失败:', formatValidation.error)
      return
    }

    // 2. 测试数据解析
    console.log('2. 测试数据解析...')
    const parseResult = parseBTable(mockBTableData)
    console.log('解析结果:', parseResult)

    if (parseResult.success) {
      console.log(`✅ 解析成功！共${parseResult.validRows}条有效记录`)
      console.log('解析的数据:')
      parseResult.data.forEach((record, index) => {
        console.log(`记录 ${index + 1}:`, {
          报修人: record.reporterName,
          联系方式: record.contact,
          地点: record.location,
          检修人: record.inspector,
          结果: record.result,
          类型: record.repairType,
          报修内容: record.repairContent,
          检修内容: record.inspectContent
        })
      })

      // 3. 测试A-B表匹配关键字生成
      console.log('3. 测试匹配关键字生成...')
      parseResult.data.forEach((record, index) => {
        const matchKey = `${record.reporterName || ''}_${record.contact || ''}`.trim()
        console.log(`记录 ${index + 1} 匹配关键字: "${matchKey}"`)
      })

    } else {
      console.error('❌ 解析失败:', parseResult.errors)
    }

  } catch (error) {
    console.error('测试过程中发生错误:', error)
  }
}

// 在浏览器控制台中运行测试
if (typeof window !== 'undefined') {
  window.testBTableParsing = testBTableParsing
  console.log('B表解析测试已准备就绪，请在浏览器控制台中运行: testBTableParsing()')
} else {
  // Node.js环境
  testBTableParsing()
}

// 导出给Node.js环境使用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { testBTableParsing, mockBTableData }
}