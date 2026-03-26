import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'providers/dashboard_provider.dart';
import 'models/dashboard_models.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final overviewAsyncValue = ref.watch(dashboardOverviewProvider);

    return Scaffold(
      body: overviewAsyncValue.when(
        data: (data) => RefreshIndicator(
          onRefresh: () => ref.refresh(dashboardOverviewProvider.future),
          child: ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              _buildMetricsGrid(context, data.metrics, data.trends),
              const SizedBox(height: 24),
              _buildSystemInfoCard(context, data.systemInfo),
            ],
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('加载失败: $err', style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.refresh(dashboardOverviewProvider),
                child: const Text('重试'),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMetricsGrid(BuildContext context, MetricsData metrics, TrendsData trends) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 16,
      mainAxisSpacing: 16,
      childAspectRatio: 1.5,
      children: [
        _MetricCard(
          title: '总任务数',
          value: metrics.totalTasks.toString(),
          trend: trends.totalTasksTrend,
          icon: Icons.task,
          color: Colors.blue,
        ),
        _MetricCard(
          title: '进行中',
          value: metrics.inProgress.toString(),
          trend: trends.inProgressTrend,
          icon: Icons.run_circle,
          color: Colors.orange,
        ),
        _MetricCard(
          title: '待处理',
          value: metrics.pending.toString(),
          trend: trends.pendingTrend,
          icon: Icons.pending_actions,
          color: Colors.amber,
        ),
        _MetricCard(
          title: '本月完成',
          value: metrics.completedThisMonth.toString(),
          trend: trends.completedTrend,
          icon: Icons.done_all,
          color: Colors.green,
        ),
      ],
    );
  }

  Widget _buildSystemInfoCard(BuildContext context, SystemInfo info) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('系统状态', style: Theme.of(context).textTheme.titleLarge),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.people),
              title: const Text('在线用户'),
              trailing: Text('${info.onlineUsers} 人'),
            ),
            ListTile(
              leading: const Icon(Icons.sync),
              title: const Text('最新数据同步'),
              trailing: Text(info.lastDataSync),
            ),
            ListTile(
              leading: const Icon(Icons.timer),
              title: const Text('系统运行时间'),
              trailing: Text(info.systemUptime),
            ),
          ],
        ),
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String title;
  final String value;
  final TrendData trend;
  final IconData icon;
  final Color color;

  const _MetricCard({
    required this.title,
    required this.value,
    required this.trend,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final isUp = trend.direction == 'up';
    final trendColor = isUp ? Colors.red : Colors.green;
    final trendIcon = isUp ? Icons.arrow_upward : Icons.arrow_downward;

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(title, style: const TextStyle(color: Colors.grey, fontSize: 14)),
                Icon(icon, color: color, size: 20),
              ],
            ),
            Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            Row(
              children: [
                Icon(trendIcon, color: trendColor, size: 16),
                const SizedBox(width: 4),
                Text(
                  '${trend.value}%',
                  style: TextStyle(color: trendColor, fontSize: 12),
                ),
              ],
            )
          ],
        ),
      ),
    );
  }
}

