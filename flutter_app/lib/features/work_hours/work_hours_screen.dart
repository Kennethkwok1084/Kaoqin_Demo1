import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'providers/work_hours_provider.dart';
import 'models/work_hour_models.dart';

class WorkHoursScreen extends ConsumerWidget {
  const WorkHoursScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final workHoursAsyncValue = ref.watch(workHoursListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('工时记录'),
        actions: [
          IconButton(
            icon: const Icon(Icons.calendar_month),
            onPressed: () {
              // TODO: 弹出日期选择器
            },
          ),
        ],
      ),
      body: workHoursAsyncValue.when(
        data: (records) => _buildRecordsList(context, ref, records),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('加载失败: $err', style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.refresh(workHoursListProvider),
                child: const Text('重试'),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRecordsList(BuildContext context, WidgetRef ref, List<WorkHourRecord> records) {
    if (records.isEmpty) {
      return RefreshIndicator(
        onRefresh: () async => ref.refresh(workHoursListProvider),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: const [
            SizedBox(height: 200),
            Center(child: Text('当前区间暂无工时记录', style: TextStyle(color: Colors.grey))),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async => ref.refresh(workHoursListProvider),
      child: ListView.builder(
        itemCount: records.length,
        padding: const EdgeInsets.all(8.0),
        itemBuilder: (context, index) {
          final record = records[index];
          return Card(
            elevation: 1,
            margin: const EdgeInsets.symmetric(vertical: 6.0, horizontal: 4.0),
            child: ListTile(
              leading: const CircleAvatar(
                backgroundColor: Colors.teal,
                child: Icon(Icons.access_time_filled, color: Colors.white),
              ),
              title: Text(record.title ?? '工时记录 - ${record.id}', style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  Text('日期: ${record.workDate ?? ''}'),
                  Text('类型: ${record.taskType ?? ""}'),
                  if (record.memberName != null) Text('成员: ${record.memberName}'),
                ],
              ),
              trailing: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '+${record.workHours ?? 0.0}h',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.green),
                  ),
                  if (record.source == 'manual')
                    const Text(
                      '手动补录',
                      style: TextStyle(fontSize: 12, color: Colors.orange),
                    ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
