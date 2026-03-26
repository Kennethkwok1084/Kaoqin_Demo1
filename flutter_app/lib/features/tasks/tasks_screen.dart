import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'providers/task_provider.dart';
import 'models/task_models.dart';

class TasksScreen extends ConsumerWidget {
  const TasksScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tasksAsyncValue = ref.watch(taskListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('我的任务'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: () {
              // TODO: 打开筛选抽屉或BottomSheet
            },
          ),
        ],
      ),
      body: tasksAsyncValue.when(
        data: (data) => _buildTaskList(context, ref, data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('加载失败: $err', style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.refresh(taskListProvider),
                child: const Text('重试'),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTaskList(BuildContext context, WidgetRef ref, PaginatedData<TaskItem> data) {
    if (data.items.isEmpty) {
      return RefreshIndicator(
        onRefresh: () async => ref.refresh(taskListProvider),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: const [
            SizedBox(height: 200),
            Center(child: Text('暂无任务数据', style: TextStyle(color: Colors.grey))),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async => ref.refresh(taskListProvider),
      child: ListView.builder(
        itemCount: data.items.length,
        padding: const EdgeInsets.all(8.0),
        itemBuilder: (context, index) {
          final task = data.items[index];
          return Card(
            elevation: 1,
            margin: const EdgeInsets.symmetric(vertical: 6.0, horizontal: 4.0),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: _getStatusColor(task.status),
                child: const Icon(Icons.build, color: Colors.white, size: 20),
              ),
              title: Text(task.title, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  if (task.location != null) 
                    Text('地点: ${task.location}'),
                  if (task.assigneeName != null)
                    Text('处理人: ${task.assigneeName}'),
                  if (task.createdAt != null)
                    Text('创建时间: ${_formatDate(task.createdAt)}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                ],
              ),
              trailing: Chip(
                label: Text(
                  _getStatusText(task.status),
                  style: const TextStyle(fontSize: 12, color: Colors.white),
                ),
                backgroundColor: _getStatusColor(task.status),
              ),
              onTap: () {
                // TODO: 路由跳转到任务详情
              },
            ),
          );
        },
      ),
    );
  }

  String _getStatusText(String? status) {
    switch (status) {
      case 'pending': return '待处理';
      case 'in_progress': return '进行中';
      case 'completed': return '已完成';
      case 'cancelled': return '已取消';
      default: return status ?? '未知';
    }
  }

  Color _getStatusColor(String? status) {
    switch (status) {
      case 'pending': return Colors.orange;
      case 'in_progress': return Colors.blue;
      case 'completed': return Colors.green;
      case 'cancelled': return Colors.grey;
      default: return Colors.grey;
    }
  }

  String _formatDate(String? rawDate) {
    if (rawDate == null) return '';
    try {
      final dt = DateTime.parse(rawDate).toLocal();
      return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} '
             '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return rawDate;
    }
  }
}

