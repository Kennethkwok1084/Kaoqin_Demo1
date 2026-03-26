import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'providers/members_provider.dart';
import 'models/member_models.dart';
import '../../shared/models/paginated_data.dart';

class MembersScreen extends ConsumerWidget {
  const MembersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final membersAsyncValue = ref.watch(membersListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('成员管理'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              // TODO: 实现搜索弹窗
            },
          )
        ],
      ),
      body: membersAsyncValue.when(
        data: (data) => _buildMembersList(context, ref, data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('加载失败: $err', style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.refresh(membersListProvider),
                child: const Text('重试'),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMembersList(BuildContext context, WidgetRef ref, PaginatedData<MemberItem> data) {
    if (data.items.isEmpty) {
      return RefreshIndicator(
        onRefresh: () async => ref.refresh(membersListProvider),
        child: ListView(
          children: const [
            SizedBox(height: 200),
            Center(child: Text('暂无成员数据')),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async => ref.refresh(membersListProvider),
      child: ListView.builder(
        itemCount: data.items.length,
        padding: const EdgeInsets.all(8.0),
        itemBuilder: (context, index) {
          final member = data.items[index];
          return Card(
            elevation: 1,
            margin: const EdgeInsets.symmetric(vertical: 4.0, horizontal: 4.0),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: member.isActive == true ? Colors.blue : Colors.grey,
                child: Text(member.name?.substring(0, 1) ?? member.username.substring(0, 1)),
              ),
              title: Text('${member.name ?? member.username} (${member.studentId ?? ""})', 
                         style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text('${member.department ?? '未分配部门'} - ${member.role ?? '员工'}'),
              trailing: Chip(
                label: Text(
                  member.statusDisplay ?? (member.isActive == true ? '在职' : '离职'),
                  style: const TextStyle(fontSize: 12),
                ),
                backgroundColor: member.isActive == true ? Colors.green.shade100 : Colors.grey.shade300,
              ),
            ),
          );
        },
      ),
    );
  }
}
