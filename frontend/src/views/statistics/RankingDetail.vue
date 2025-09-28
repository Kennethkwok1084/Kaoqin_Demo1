<template>
  <div class="ranking-detail">
    <div class="page-header">
      <div class="header-left">
        <el-button type="text" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回统计报表
        </el-button>
        <h1 class="page-title">成员排行榜</h1>
        <p class="page-description">查看更多成员绩效和工时排行榜数据</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Refresh" :loading="loading" @click="loadRankingData">
          刷新数据
        </el-button>
      </div>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true">
        <el-form-item label="统计区间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="loadRankingData"
          />
        </el-form-item>
        <el-form-item label="排行维度">
          <el-select v-model="metric" @change="loadRankingData">
            <el-option label="综合评分" value="comprehensive_score" />
            <el-option label="完成任务数" value="completed_tasks" />
            <el-option label="总工时" value="work_hours" />
            <el-option label="效率评分" value="efficiency" />
          </el-select>
        </el-form-item>
        <el-form-item label="显示数量">
          <el-select v-model="limit" @change="loadRankingData">
            <el-option label="前 20 名" :value="20" />
            <el-option label="前 50 名" :value="50" />
            <el-option label="前 100 名" :value="100" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="table-header">
          <span>成员排行榜（共 {{ rankingData.length }} 人）</span>
        </div>
      </template>
      <el-table :data="rankingData" v-loading="loading" stripe height="600">
        <el-table-column prop="rank" label="排名" width="80" />
        <el-table-column label="成员" min-width="200">
          <template #default="{ row }">
            <div class="member-info">
              <el-avatar
                :src="row.avatar"
                :size="36"
                :style="{ backgroundColor: getAvatarColor(row.memberName) }"
              >
                {{ row.memberName?.charAt(0) }}
              </el-avatar>
              <div class="member-meta">
                <div class="member-name">{{ row.memberName }}</div>
                <div class="member-dept">{{ row.department || '未分配部门' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="综合评分" width="120">
          <template #default="{ row }">
            <el-tag type="success">{{ row.score }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="completedTasks" label="完成任务" width="120" />
        <el-table-column prop="workHours" label="工时 (h)" width="120">
          <template #default="{ row }">{{ (row.workHours ?? 0).toFixed(1) }}</template>
        </el-table-column>
        <el-table-column prop="efficiency" label="效率" width="120">
          <template #default="{ row }">{{ (row.efficiency ?? 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="change" label="排名变化" width="120">
          <template #default="{ row }">
            <el-tag :type="getRankTagType(row.change)">
              <el-icon v-if="row.change > 0"><CaretTop /></el-icon>
              <el-icon v-else-if="row.change < 0"><CaretBottom /></el-icon>
              <el-icon v-else><Minus /></el-icon>
              {{ formatRankChange(row.change) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, ArrowLeft, CaretTop, CaretBottom, Minus } from '@element-plus/icons-vue'
import { statisticsApi } from '@/api/statistics'
import type { MemberRankingItem } from '@/types/statistics'
import { getMonthRange } from '@/utils/date'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const rankingData = ref<MemberRankingItem[]>([])
const metric = ref('comprehensive_score')
const limit = ref(50)
const defaultRange = getMonthRange()
const dateRange = ref<[string, string]>([
  (route.query.start as string) || defaultRange[0],
  (route.query.end as string) || defaultRange[1]
])

const loadRankingData = async () => {
  if (!dateRange.value || dateRange.value.length !== 2) {
    ElMessage.warning('请选择有效的统计区间')
    return
  }

  try {
    loading.value = true
    const data = await statisticsApi.getRankingData({
      type: 'members',
      metric: metric.value,
      period_start: dateRange.value[0],
      period_end: dateRange.value[1],
      limit: limit.value
    })
    rankingData.value = data
  } catch (error) {
    console.error('加载排行榜失败:', error)
    ElMessage.error('加载排行榜失败')
  } finally {
    loading.value = false
  }
}

const formatRankChange = (change: number) => {
  if (change > 0) return `+${change}`
  if (change < 0) return change
  return '0'
}

const getRankTagType = (change: number) => {
  if (change > 0) return 'success'
  if (change < 0) return 'danger'
  return 'info'
}

const getAvatarColor = (name: string) => {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
  const hash =
    name?.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) || 0
  return colors[hash % colors.length]
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  loadRankingData()
})
</script>

<style scoped lang="scss">
.ranking-detail {
  padding: 24px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;

    .header-left {
      .page-title {
        margin: 8px 0 4px 0;
        font-size: 24px;
        font-weight: 600;
      }

      .page-description {
        margin: 0;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .filter-card {
    margin-bottom: 16px;
  }

  .member-info {
    display: flex;
    align-items: center;
    gap: 12px;

    .member-meta {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .member-name {
        font-weight: 600;
      }

      .member-dept {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
