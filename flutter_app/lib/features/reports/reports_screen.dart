import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'providers/reports_provider.dart';
import 'models/report_models.dart';

class ReportsScreen extends ConsumerWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final overviewAsyncValue = ref.watch(statisticsOverviewProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('统计报表'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(statisticsOverviewProvider.notifier).refresh(),
          )
        ],
      ),
      body: overviewAsyncValue.when(
        data: (data) => _buildOverviewGrid(context, data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('加载失败: $err', style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.read(statisticsOverviewProvider.notifier).refresh(),
                child: const Text('重试'),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOverviewGrid(BuildContext context, StatisticsOverview data) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        _buildSectionTitle('工时统计'),
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          crossAxisSpacing: 16.0,
          mainAxisSpacing: 16.0,
          childAspectRatio: 1.5,
          children: [
            _buildStatCard('总工时', '${data.attendance.totalWorkHours}h', Icons.timer),
            _buildStatCard('平均工时', '${data.attendance.avgWorkHours}h', Icons.query_stats),
            _buildStatCard('迟到率', '${data.attendance.lateRate}%', Icons.warning_amber),
            _buildStatCard('总打卡记录', '${data.attendance.totalRecords}', Icons.how_to_reg),
          ],
        ),
        const SizedBox(height: 24),
        _buildSectionTitle('任务统计'),
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          crossAxisSpacing: 16.0,
          mainAxisSpacing: 16.0,
          childAspectRatio: 1.5,
          children: [
            _buildStatCard('总任务数', '${data.tasks.total}', Icons.task),
            _buildStatCard('完成率', '${data.tasks.completionRate}%', Icons.check_circle_outline),
            _buildStatCard('进行中', '${data.tasks.inProgress}', Icons.pending_actions),
            _buildStatCard('待处理', '${data.tasks.pending}', Icons.queue),
          ],
        ),
        const SizedBox(height: 24),
        _buildSectionTitle('成员统计'),
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          crossAxisSpacing: 16.0,
          mainAxisSpacing: 16.0,
          childAspectRatio: 1.5,
          children: [
            _buildStatCard('总人数', '${data.members.total}', Icons.people),
            _buildStatCard('在职人数', '${data.members.active}', Icons.person_pin),
          ],
        ),
      ],
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: Text(
        title,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, size: 20, color: Colors.blueGrey),
                const SizedBox(width: 8),
                Text(title, style: const TextStyle(color: Colors.grey)),
              ],
            ),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }
}
