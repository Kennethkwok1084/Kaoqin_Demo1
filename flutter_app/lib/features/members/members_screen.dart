import 'dart:io';

import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/app_strings.dart';
import '../../shared/models/paginated_data.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/app_metric_card.dart';
import '../../shared/widgets/desktop_page.dart';
import '../../shared/widgets/glass_panel.dart';
import '../auth/providers/auth_provider.dart';
import 'models/member_models.dart';
import 'providers/members_provider.dart';

class MembersScreen extends ConsumerStatefulWidget {
  const MembersScreen({super.key});

  @override
  ConsumerState<MembersScreen> createState() => _MembersScreenState();
}

class _MembersScreenState extends ConsumerState<MembersScreen> {
  late final TextEditingController _searchController;
  late final TextEditingController _departmentController;
  late final TextEditingController _classController;
  String? _selectedRole;
  bool? _selectedActive;
  int? _busyMemberId;
  bool _batchBusy = false;
  final Set<int> _selectedMemberIds = <int>{};

  @override
  void initState() {
    super.initState();
    final params = ref.read(membersParamsProvider);
    _searchController = TextEditingController(text: params.search ?? '');
    _departmentController = TextEditingController(text: params.department ?? '');
    _classController = TextEditingController(text: params.className ?? '');
    _selectedRole = params.role;
    _selectedActive = params.isActive;
  }

  @override
  void dispose() {
    _searchController.dispose();
    _departmentController.dispose();
    _classController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final params = ref.watch(membersParamsProvider);
    final membersAsync = ref.watch(membersListProvider);
    final stats = ref.watch(memberStatsProvider).asData?.value;
    final currentUserId = _asInt(ref.watch(authStateProvider).asData?.value?['id']);

    return DesktopPage(
      title: s.membersTitle,
      subtitle: s.membersSubtitle,
      actions: [
        OutlinedButton.icon(
          onPressed: _refresh,
          icon: const Icon(Icons.refresh_rounded),
          label: Text(s.refresh),
        ),
        const SizedBox(width: 12),
        OutlinedButton.icon(
          onPressed: _importMembers,
          icon: const Icon(Icons.upload_file_rounded),
          label: Text(_t(s, '导入 Excel', 'Import Excel')),
        ),
        const SizedBox(width: 12),
        OutlinedButton.icon(
          onPressed: (_selectedMemberIds.isEmpty || _batchBusy) ? null : _batchLeaveMembers,
          icon: const Icon(Icons.person_off_outlined),
          label: Text(_t(s, '批量离职', 'Batch leave')),
        ),
        const SizedBox(width: 12),
        OutlinedButton.icon(
          onPressed: (_selectedMemberIds.isEmpty || _batchBusy) ? null : _batchDeleteMembers,
          style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger),
          icon: const Icon(Icons.delete_sweep_outlined),
          label: Text(_t(s, '批量删除', 'Batch delete')),
        ),
        const SizedBox(width: 12),
        FilledButton.icon(
          onPressed: _createMember,
          icon: const Icon(Icons.person_add_alt_1_rounded),
          label: Text(_t(s, '新增成员', 'New member')),
        ),
      ],
      children: [
        GlassPanel(
          child: LayoutBuilder(
            builder: (context, constraints) {
              const spacing = 12.0;
              final columns = constraints.maxWidth >= 1500
                  ? 5
                  : constraints.maxWidth >= 980
                      ? 3
                      : constraints.maxWidth >= 640
                          ? 2
                          : 1;
              final fieldWidth = columns == 1
                  ? constraints.maxWidth
                  : (constraints.maxWidth - spacing * (columns - 1)) / columns;

              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: spacing,
                    runSpacing: 12,
                    children: [
                      SizedBox(
                        width: fieldWidth,
                        child: TextField(
                          controller: _searchController,
                          onSubmitted: (_) => _applyFilters(),
                          decoration: InputDecoration(
                            labelText: _t(s, '搜索', 'Search'),
                            hintText: _t(s, '姓名、学号、用户名', 'Name, student ID, username'),
                            prefixIcon: const Icon(Icons.search_rounded),
                          ),
                        ),
                      ),
                      SizedBox(
                        width: fieldWidth,
                        child: DropdownButtonFormField<String?>(
                          initialValue: _selectedRole,
                          decoration: InputDecoration(labelText: s.role),
                          items: _roleFilterItems(s),
                          onChanged: (value) => setState(() => _selectedRole = value),
                        ),
                      ),
                      SizedBox(
                        width: fieldWidth,
                        child: DropdownButtonFormField<bool?>(
                          initialValue: _selectedActive,
                          decoration: InputDecoration(labelText: s.status),
                          items: [
                            DropdownMenuItem<bool?>(value: null, child: Text(_t(s, '全部状态', 'All statuses'))),
                            DropdownMenuItem<bool?>(value: true, child: Text(_t(s, '启用中', 'Active'))),
                            DropdownMenuItem<bool?>(value: false, child: Text(_t(s, '已停用', 'Inactive'))),
                          ],
                          onChanged: (value) => setState(() => _selectedActive = value),
                        ),
                      ),
                      SizedBox(
                        width: fieldWidth,
                        child: TextField(
                          controller: _departmentController,
                          onSubmitted: (_) => _applyFilters(),
                          decoration: InputDecoration(
                            labelText: s.department,
                            hintText: _t(s, '按部门筛选', 'Filter by department'),
                          ),
                        ),
                      ),
                      SizedBox(
                        width: fieldWidth,
                        child: TextField(
                          controller: _classController,
                          onSubmitted: (_) => _applyFilters(),
                          decoration: InputDecoration(
                            labelText: s.classLabel,
                            hintText: _t(s, '按班级筛选', 'Filter by class'),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: [
                      OutlinedButton.icon(
                        onPressed: _resetFilters,
                        icon: const Icon(Icons.filter_alt_off_outlined),
                        label: Text(s.resetFilters),
                      ),
                      FilledButton.icon(
                        onPressed: _applyFilters,
                        icon: const Icon(Icons.filter_alt_rounded),
                        label: Text(_t(s, '应用筛选', 'Apply filters')),
                      ),
                    ],
                  ),
                ],
              );
            },
          ),
        ),
        const SizedBox(height: 20),
        membersAsync.when(
          data: (data) {
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (!mounted) return;
              final visibleIds = data.items.map((item) => item.id).toSet();
              final nextSelected = _selectedMemberIds.where(visibleIds.contains).toSet();
              if (nextSelected.length != _selectedMemberIds.length) {
                setState(() {
                  _selectedMemberIds
                    ..clear()
                    ..addAll(nextSelected);
                });
              }
            });
            return _MembersBody(
              data: data,
              stats: stats,
              currentPage: params.page,
              busyMemberId: _busyMemberId,
              currentUserId: currentUserId,
              batchBusy: _batchBusy,
              selectedMemberIds: _selectedMemberIds,
              onToggleSelection: _toggleSelection,
              onToggleSelectAllVisible: () => _toggleSelectAllVisible(data.items, currentUserId),
              onClearSelection: _clearSelection,
              onPageChanged: (page) => ref.read(membersParamsProvider.notifier).setPage(page),
              onEdit: _editMember,
              onPassword: _changePassword,
              onToggleActive: _toggleActive,
              onDelete: _deleteMember,
            );
          },
          loading: () => DesktopStatusView(
            icon: Icons.people_outline_rounded,
            title: s.loadingMembers,
            message: s.loadingMembersMsg,
          ),
          error: (error, stack) => DesktopStatusView(
            icon: Icons.error_outline_rounded,
            title: s.membersUnavailable,
            message: _readableError(error, s),
            action: FilledButton(onPressed: _refresh, child: Text(s.retry)),
          ),
        ),
      ],
    );
  }

  void _applyFilters() {
    ref.read(membersParamsProvider.notifier).applyFilters(
          search: _searchController.text,
          role: _selectedRole,
          isActive: _selectedActive,
          department: _departmentController.text,
          className: _classController.text,
        );
  }

  void _resetFilters() {
    _searchController.clear();
    _departmentController.clear();
    _classController.clear();
    setState(() {
      _selectedRole = null;
      _selectedActive = null;
    });
    ref.read(membersParamsProvider.notifier).resetFilters();
  }

  void _refresh() {
    _clearSelection();
    ref.invalidate(membersListProvider);
    ref.invalidate(memberStatsProvider);
  }

  void _toggleSelection(int memberId, bool selected) {
    setState(() {
      if (selected) {
        _selectedMemberIds.add(memberId);
      } else {
        _selectedMemberIds.remove(memberId);
      }
    });
  }

  void _clearSelection() {
    if (_selectedMemberIds.isEmpty) return;
    setState(_selectedMemberIds.clear);
  }

  void _toggleSelectAllVisible(List<MemberItem> members, int? currentUserId) {
    final selectableIds = members
        .where((member) => currentUserId == null || member.id != currentUserId)
        .map((member) => member.id)
        .toSet();
    final allSelected = selectableIds.isNotEmpty && selectableIds.every(_selectedMemberIds.contains);
    setState(() {
      if (allSelected) {
        _selectedMemberIds.removeAll(selectableIds);
      } else {
        _selectedMemberIds.addAll(selectableIds);
      }
    });
  }

  Future<void> _createMember() async {
    final created = await showDialog<bool>(
      context: context,
      useRootNavigator: true,
      builder: (_) => const _MemberFormDialog(),
    );
    if (!mounted || created != true) return;
    _refresh();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(_t(context.strings, '成员创建成功', 'Member created'))),
    );
  }

  Future<void> _importMembers() async {
    final result = await showDialog<MemberImportResult>(
      context: context,
      useRootNavigator: true,
      builder: (_) => const _MemberImportDialog(),
    );
    if (!mounted || result == null) return;
    _refresh();
    final s = context.strings;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          _t(
            s,
            '导入完成：成功 ${result.successfulImports} 条，失败 ${result.failedImports} 条，跳过 ${result.skippedDuplicates} 条',
            'Import finished: ${result.successfulImports} succeeded, ${result.failedImports} failed, ${result.skippedDuplicates} skipped.',
          ),
        ),
      ),
    );
  }

  Future<void> _editMember(MemberItem member) async {
    final updated = await showDialog<bool>(
      context: context,
      useRootNavigator: true,
      builder: (_) => _MemberFormDialog(member: member),
    );
    if (!mounted || updated != true) return;
    _refresh();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(_t(context.strings, '成员信息已更新', 'Member updated'))),
    );
  }

  Future<void> _changePassword(MemberItem member) async {
    final currentUserId = _asInt(ref.read(authStateProvider).asData?.value?['id']);
    final payload = await showDialog<_PasswordValue>(
      context: context,
      useRootNavigator: true,
      builder: (_) => _PasswordDialog(requireOldPassword: currentUserId == member.id),
    );
    if (!mounted || payload == null) return;
    await _runCommand(
      memberId: member.id,
      successMessage: _t(context.strings, '密码已更新', 'Password updated'),
      command: (service) => service.changePassword(
        memberId: member.id,
        oldPassword: payload.oldPassword,
        newPassword: payload.newPassword,
      ),
    );
  }

  Future<void> _toggleActive(MemberItem member) async {
    final nextActive = !(member.isActive ?? false);
    await _runCommand(
      memberId: member.id,
      successMessage: nextActive
          ? _t(context.strings, '成员已启用', 'Member enabled')
          : _t(context.strings, '成员已停用', 'Member disabled'),
      command: (service) => service.updateMember(member.id, {'is_active': nextActive}),
    );
  }

  Future<void> _deleteMember(MemberItem member) async {
    final s = context.strings;
    final confirmed = await showDialog<bool>(
      context: context,
      useRootNavigator: true,
      builder: (dialogContext) => AlertDialog(
        title: Text(_t(s, '删除成员', 'Delete member')),
        content: Text(
          _t(
            s,
            '确认删除 ${_memberName(member)} 吗？该操作会调用真实删除接口。',
            'Delete ${_memberName(member)}? This will call the real delete API.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text(_t(s, '取消', 'Cancel')),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(_t(s, '删除', 'Delete')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    await _runCommand(
      memberId: member.id,
      successMessage: _t(s, '成员已删除', 'Member deleted'),
      command: (service) => service.deleteMember(member.id),
    );
  }

  Future<void> _batchLeaveMembers() async {
    await _runBatchAction(
      title: _t(context.strings, '批量离职', 'Batch leave'),
      content: _t(
        context.strings,
        '将选中的 ${_selectedMemberIds.length} 名成员标记为离职。该操作会逐条调用现有更新接口，执行过程中部分成功、部分失败是可能结果。',
        'Mark ${_selectedMemberIds.length} selected members as inactive. This uses the existing update API one by one, so partial success is possible.',
      ),
      successLabel: _t(context.strings, '批量离职完成', 'Batch leave completed'),
      command: (service, member) => service.updateMember(member.id, {'is_active': false}),
    );
  }

  Future<void> _batchDeleteMembers() async {
    await _runBatchAction(
      title: _t(context.strings, '批量删除成员', 'Batch delete members'),
      content: _t(
        context.strings,
        '将删除选中的 ${_selectedMemberIds.length} 名成员。该操作会逐条调用现有删除接口，执行过程中部分成功、部分失败是可能结果。',
        'Delete ${_selectedMemberIds.length} selected members. This uses the existing delete API one by one, so partial success is possible.',
      ),
      successLabel: _t(context.strings, '批量删除完成', 'Batch delete completed'),
      danger: true,
      command: (service, member) => service.deleteMember(member.id),
    );
  }

  Future<void> _runBatchAction({
    required String title,
    required String content,
    required String successLabel,
    bool danger = false,
    required Future<void> Function(MembersCommandService service, MemberItem member) command,
  }) async {
    final s = context.strings;
    final data = ref.read(membersListProvider).asData?.value;
    if (data == null || _selectedMemberIds.isEmpty) return;

    final selectedMembers = data.items
        .where((member) => _selectedMemberIds.contains(member.id))
        .toList(growable: false);
    if (selectedMembers.isEmpty) return;

    final confirmed = await showDialog<bool>(
      context: context,
      useRootNavigator: true,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text(_t(s, '取消', 'Cancel')),
          ),
          FilledButton(
            style: danger ? FilledButton.styleFrom(backgroundColor: AppColors.danger) : null,
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(_t(s, '确认执行', 'Confirm')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    final service = ref.read(membersCommandProvider);
    int successCount = 0;
    int failedCount = 0;
    final failures = <String>[];

    setState(() => _batchBusy = true);
    try {
      for (final member in selectedMembers) {
        try {
          await command(service, member);
          successCount += 1;
        } catch (error) {
          failedCount += 1;
          failures.add('${_memberName(member)}：${_readableError(error, s)}');
        }
      }
      _refresh();
      if (!mounted) return;
      final summary = _t(
        s,
        '$successLabel：成功 $successCount 条，失败 $failedCount 条',
        '$successLabel: $successCount succeeded, $failedCount failed',
      );
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: failedCount == 0 ? null : AppColors.warning,
          content: Text(
            failures.isEmpty ? summary : '$summary\n${failures.take(2).join('；')}',
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _batchBusy = false);
      }
    }
  }

  Future<void> _runCommand({
    int? memberId,
    required String successMessage,
    required Future<dynamic> Function(MembersCommandService service) command,
  }) async {
    final service = ref.read(membersCommandProvider);
    if (memberId != null) {
      setState(() => _busyMemberId = memberId);
    }
    try {
      await command(service);
      _refresh();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(successMessage)));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_readableError(error, context.strings)),
            backgroundColor: AppColors.danger,
          ),
        );
      }
    } finally {
      if (mounted && memberId != null) {
        setState(() => _busyMemberId = null);
      }
    }
  }
}

class _MembersBody extends StatelessWidget {
  const _MembersBody({
    required this.data,
    required this.stats,
    required this.currentPage,
    required this.busyMemberId,
    required this.currentUserId,
    required this.batchBusy,
    required this.selectedMemberIds,
    required this.onToggleSelection,
    required this.onToggleSelectAllVisible,
    required this.onClearSelection,
    required this.onPageChanged,
    required this.onEdit,
    required this.onPassword,
    required this.onToggleActive,
    required this.onDelete,
  });

  final PaginatedData<MemberItem> data;
  final MemberStats? stats;
  final int currentPage;
  final int? busyMemberId;
  final int? currentUserId;
  final bool batchBusy;
  final Set<int> selectedMemberIds;
  final void Function(int memberId, bool selected) onToggleSelection;
  final VoidCallback onToggleSelectAllVisible;
  final VoidCallback onClearSelection;
  final ValueChanged<int> onPageChanged;
  final ValueChanged<MemberItem> onEdit;
  final ValueChanged<MemberItem> onPassword;
  final ValueChanged<MemberItem> onToggleActive;
  final ValueChanged<MemberItem> onDelete;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    if (data.items.isEmpty) {
      return DesktopStatusView(
        icon: Icons.person_off_outlined,
        title: s.noMembers,
        message: s.noMembersMsg,
      );
    }

    final visibleActiveCount = data.items.where((m) => m.isActive == true).length;
    final selectableItems = data.items
        .where((m) => currentUserId == null || m.id != currentUserId)
        .toList(growable: false);
    final allVisibleSelected = selectableItems.isNotEmpty &&
        selectableItems.every((member) => selectedMemberIds.contains(member.id));
    final departmentCount = data.items
        .map((m) => m.department)
        .whereType<String>()
        .where((v) => v.trim().isNotEmpty)
        .toSet()
        .length;

    return Column(
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            final columns = constraints.maxWidth >= 1180 ? 4 : constraints.maxWidth >= 720 ? 2 : 1;
            return GridView.count(
              crossAxisCount: columns,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              childAspectRatio: 1.45,
              children: [
                AppMetricCard(title: s.visibleMembers, value: '${data.items.length}', icon: Icons.people_alt_outlined, tint: AppColors.accent, caption: s.totalCount(stats?.totalMembers ?? data.total)),
                AppMetricCard(title: s.active, value: '${stats?.activeMembers ?? visibleActiveCount}', icon: Icons.verified_user_outlined, tint: AppColors.success, caption: stats != null ? _t(s, '来自后端统计', 'From backend stats') : _t(s, '当前页启用成员', 'Active on this page')),
                AppMetricCard(title: s.departments, value: '$departmentCount', icon: Icons.domain_rounded, tint: AppColors.warning, caption: _t(s, '当前页可见部门', 'Visible departments')),
                AppMetricCard(title: s.currentPage, value: '${data.page}', icon: Icons.view_day_outlined, tint: AppColors.textSecondary, caption: stats != null ? _t(s, '停用 ${stats!.inactiveMembers} 人', '${stats!.inactiveMembers} inactive') : s.pages(data.totalPages ?? 1)),
              ],
            );
          },
        ),
        const SizedBox(height: 24),
        if (selectedMemberIds.isNotEmpty) ...[
          GlassPanel(
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    _t(
                      s,
                      '已选择 ${selectedMemberIds.length} 名成员，可执行批量离职或批量删除。当前前端会逐条调用现有接口，不是事务型批处理。',
                      '${selectedMemberIds.length} members selected. Batch actions call the existing APIs one by one and are not transactional.',
                    ),
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
                const SizedBox(width: 12),
                OutlinedButton(
                  onPressed: batchBusy ? null : onToggleSelectAllVisible,
                  child: Text(allVisibleSelected ? _t(s, '取消全选', 'Clear visible') : _t(s, '全选当前页', 'Select visible')),
                ),
                const SizedBox(width: 8),
                TextButton(
                  onPressed: batchBusy ? null : onClearSelection,
                  child: Text(_t(s, '清空选择', 'Clear selection')),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],
        LayoutBuilder(
          builder: (context, constraints) {
            final columns = constraints.maxWidth >= 1320 ? 3 : constraints.maxWidth >= 860 ? 2 : 1;
            return GridView.builder(
              itemCount: data.items.length,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: columns,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                childAspectRatio: constraints.maxWidth >= 1320 ? 1.18 : 1.02,
              ),
              itemBuilder: (context, index) {
                final member = data.items[index];
                return _MemberCard(
                  member: member,
                  isCurrentUser: currentUserId == member.id,
                  busy: busyMemberId == member.id,
                  selectable: currentUserId != member.id,
                  selected: selectedMemberIds.contains(member.id),
                  batchBusy: batchBusy,
                  onSelectedChanged: (selected) => onToggleSelection(member.id, selected),
                  onEdit: () => onEdit(member),
                  onPassword: () => onPassword(member),
                  onToggleActive: () => onToggleActive(member),
                  onDelete: () => onDelete(member),
                );
              },
            );
          },
        ),
        const SizedBox(height: 20),
        Row(
          children: [
            Text(_t(s, '共 ${data.total} 名成员', '${data.total} members'), style: Theme.of(context).textTheme.bodySmall),
            const Spacer(),
            OutlinedButton(onPressed: currentPage > 1 ? () => onPageChanged(currentPage - 1) : null, child: Text(s.previousPage)),
            const SizedBox(width: 8),
            ..._pageWindow(currentPage, data.totalPages ?? 1).map(
              (page) => Padding(
                padding: const EdgeInsets.only(right: 8),
                child: page == currentPage
                    ? FilledButton(onPressed: () => onPageChanged(page), child: Text('$page'))
                    : OutlinedButton(onPressed: () => onPageChanged(page), child: Text('$page')),
              ),
            ),
            OutlinedButton(
              onPressed: currentPage < (data.totalPages ?? 1) ? () => onPageChanged(currentPage + 1) : null,
              child: Text(s.nextPage),
            ),
          ],
        ),
      ],
    );
  }
}

class _MemberCard extends StatelessWidget {
  const _MemberCard({
    required this.member,
    required this.isCurrentUser,
    required this.busy,
    required this.selectable,
    required this.selected,
    required this.batchBusy,
    required this.onSelectedChanged,
    required this.onEdit,
    required this.onPassword,
    required this.onToggleActive,
    required this.onDelete,
  });

  final MemberItem member;
  final bool isCurrentUser;
  final bool busy;
  final bool selectable;
  final bool selected;
  final bool batchBusy;
  final ValueChanged<bool> onSelectedChanged;
  final VoidCallback onEdit;
  final VoidCallback onPassword;
  final VoidCallback onToggleActive;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final isActive = member.isActive == true;
    final displayName = _memberName(member);
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: isActive ? const [AppColors.accent, Color(0xFF635BFF)] : const [Color(0xFF94A3B8), Color(0xFFCBD5E1)]),
                  borderRadius: BorderRadius.circular(16),
                ),
                alignment: Alignment.center,
                child: Text(displayName.substring(0, 1).toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
              ),
              const Spacer(),
              if (selectable)
                Checkbox(
                  value: selected,
                  onChanged: (busy || batchBusy) ? null : (value) => onSelectedChanged(value ?? false),
                ),
              _StatusChip(label: member.statusDisplay ?? (isActive ? s.active : s.inactive), color: isActive ? AppColors.success : AppColors.textSecondary),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(child: Text(displayName, maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.titleMedium)),
              if (isCurrentUser) _StatusChip(label: _t(s, '当前账号', 'Current user'), color: AppColors.accent),
            ],
          ),
          const SizedBox(height: 6),
          Text(member.studentId ?? member.username, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 18),
          _InfoRow(label: s.role, value: _roleLabel(s, member.role)),
          _InfoRow(label: s.department, value: member.department ?? s.unassignedDepartment),
          _InfoRow(label: s.classLabel, value: member.className ?? s.na),
          _InfoRow(label: s.phone, value: member.phone ?? s.na),
          _InfoRow(label: _t(s, '加入日期', 'Join date'), value: _formatDate(member.joinDate)),
          const Spacer(),
          if (busy)
            const Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)))
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _ActionChip(icon: Icons.edit_outlined, label: _t(s, '编辑', 'Edit'), onTap: onEdit),
                _ActionChip(icon: Icons.lock_outline_rounded, label: _t(s, '改密', 'Password'), onTap: onPassword),
                _ActionChip(icon: isActive ? Icons.pause_circle_outline_rounded : Icons.play_circle_outline_rounded, label: isActive ? _t(s, '停用', 'Disable') : _t(s, '启用', 'Enable'), onTap: onToggleActive),
                _ActionChip(icon: Icons.delete_outline_rounded, label: _t(s, '删除', 'Delete'), onTap: onDelete, danger: true),
              ],
            ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(width: 92, child: Text(label, style: Theme.of(context).textTheme.bodySmall)),
          Expanded(child: Text(value, maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600))),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(999)),
      child: Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: color, fontWeight: FontWeight.w700)),
    );
  }
}

class _ActionChip extends StatelessWidget {
  const _ActionChip({
    required this.icon,
    required this.label,
    required this.onTap,
    this.danger = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    final foreground = danger ? AppColors.danger : AppColors.textPrimary;
    final border = danger ? AppColors.danger.withValues(alpha: 0.2) : AppColors.borderStrong;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: AppColors.surfaceStrong,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: foreground),
            const SizedBox(width: 6),
            Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: foreground, fontWeight: FontWeight.w700)),
          ],
        ),
      ),
    );
  }
}

class _MemberFormDialog extends ConsumerStatefulWidget {
  const _MemberFormDialog({this.member});

  final MemberItem? member;

  @override
  ConsumerState<_MemberFormDialog> createState() => _MemberFormDialogState();
}

class _MemberFormDialogState extends ConsumerState<_MemberFormDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _usernameController;
  late final TextEditingController _nameController;
  late final TextEditingController _studentIdController;
  late final TextEditingController _phoneController;
  late final TextEditingController _departmentController;
  late final TextEditingController _classController;
  late final TextEditingController _passwordController;
  late String _role;
  late bool _isActive;
  bool _submitting = false;
  String? _formError;
  Map<String, String> _fieldErrors = const <String, String>{};

  bool get _isEdit => widget.member != null;

  @override
  void initState() {
    super.initState();
    final member = widget.member;
    _usernameController = TextEditingController(text: member?.username ?? '');
    _nameController = TextEditingController(text: member?.name ?? '');
    _studentIdController = TextEditingController(text: member?.studentId ?? '');
    _phoneController = TextEditingController(text: member?.phone ?? '');
    _departmentController = TextEditingController(text: member?.department ?? '');
    _classController = TextEditingController(text: member?.className ?? '');
    _passwordController = TextEditingController(text: '123456');
    _role = member?.role ?? 'member';
    _isActive = member?.isActive ?? true;
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _nameController.dispose();
    _studentIdController.dispose();
    _phoneController.dispose();
    _departmentController.dispose();
    _classController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  MembersCommandService get _service => ref.read(membersCommandProvider);

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    return AlertDialog(
      title: Text(_isEdit ? _t(s, '编辑成员', 'Edit member') : _t(s, '新增成员', 'New member')),
      content: SizedBox(
        width: 560,
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _twoColumn(
                  TextFormField(
                    controller: _usernameController,
                    decoration: InputDecoration(
                      labelText: _t(s, '用户名', 'Username'),
                      errorText: _fieldErrors['username'],
                    ),
                    onChanged: (_) => _clearFieldError('username'),
                    validator: (value) {
                      final input = value?.trim() ?? '';
                      if (input.isEmpty) return _t(s, '请输入用户名', 'Enter a username');
                      if (!RegExp(r'^[A-Za-z0-9_]+$').hasMatch(input)) {
                        return _t(s, '仅支持字母、数字和下划线', 'Letters, numbers, and underscore only');
                      }
                      return null;
                    },
                  ),
                  TextFormField(
                    controller: _nameController,
                    decoration: InputDecoration(
                      labelText: _t(s, '姓名', 'Name'),
                      errorText: _fieldErrors['name'],
                    ),
                    onChanged: (_) => _clearFieldError('name'),
                    validator: (value) {
                      final input = value?.trim() ?? '';
                      if (input.isEmpty) return _t(s, '请输入姓名', 'Enter a name');
                      if (!RegExp(r'^[\u4e00-\u9fa5a-zA-Z·\s]+$').hasMatch(input)) {
                        return _t(
                          s,
                          '姓名只能包含中文、字母、空格和·符号',
                          'Name can only contain Chinese characters, letters, spaces, and middle dot.',
                        );
                      }
                      return null;
                    },
                  ),
                ),
                const SizedBox(height: 12),
                _twoColumn(
                  TextFormField(
                    controller: _studentIdController,
                    decoration: InputDecoration(
                      labelText: _t(s, '学号', 'Student ID'),
                      errorText: _fieldErrors['student_id'],
                    ),
                    onChanged: (_) => _clearFieldError('student_id'),
                    validator: (value) {
                      final input = value?.trim() ?? '';
                      if (input.isNotEmpty && !RegExp(r'^[A-Za-z0-9]+$').hasMatch(input)) {
                        return _t(s, '学号仅支持字母和数字', 'Student ID must be alphanumeric');
                      }
                      return null;
                    },
                  ),
                  TextFormField(
                    controller: _phoneController,
                    decoration: InputDecoration(
                      labelText: s.phone,
                      errorText: _fieldErrors['phone'],
                    ),
                    onChanged: (_) => _clearFieldError('phone'),
                    validator: (value) {
                      final input = value?.trim() ?? '';
                      if (input.isNotEmpty && !RegExp(r'^\d{11}$').hasMatch(input)) {
                        return _t(s, '手机号需为 11 位数字', 'Phone must be 11 digits');
                      }
                      return null;
                    },
                  ),
                ),
                const SizedBox(height: 12),
                _twoColumn(
                  TextFormField(
                    controller: _departmentController,
                    decoration: InputDecoration(
                      labelText: s.department,
                      errorText: _fieldErrors['department'],
                    ),
                    onChanged: (_) => _clearFieldError('department'),
                    validator: (value) => (value?.trim().isEmpty ?? true) ? _t(s, '请输入部门', 'Enter a department') : null,
                  ),
                  TextFormField(
                    controller: _classController,
                    decoration: InputDecoration(
                      labelText: s.classLabel,
                      errorText: _fieldErrors['class_name'],
                    ),
                    onChanged: (_) => _clearFieldError('class_name'),
                    validator: (value) => (value?.trim().isEmpty ?? true) ? _t(s, '请输入班级', 'Enter a class') : null,
                  ),
                ),
                const SizedBox(height: 12),
                _twoColumn(
                  DropdownButtonFormField<String>(
                    initialValue: _role,
                    decoration: InputDecoration(
                      labelText: s.role,
                      errorText: _fieldErrors['role'],
                    ),
                    items: _roleItems(s),
                    onChanged: (value) {
                      if (value != null) {
                        setState(() {
                          _role = value;
                          _fieldErrors = {..._fieldErrors}..remove('role');
                        });
                      }
                    },
                  ),
                  _isEdit
                      ? SwitchListTile(
                          value: _isActive,
                          contentPadding: EdgeInsets.zero,
                          title: Text(_t(s, '启用状态', 'Active status')),
                          onChanged: (value) => setState(() => _isActive = value),
                        )
                      : TextFormField(
                          controller: _passwordController,
                          obscureText: true,
                          decoration: InputDecoration(
                            labelText: _t(s, '初始密码', 'Initial password'),
                            errorText: _fieldErrors['password'],
                          ),
                          onChanged: (_) => _clearFieldError('password'),
                          validator: (value) => (value?.trim().length ?? 0) < 6 ? _t(s, '密码至少 6 位', 'Password must be at least 6 characters') : null,
                        ),
                ),
                if (!_isEdit)
                  SwitchListTile(
                    value: _isActive,
                    contentPadding: EdgeInsets.zero,
                    title: Text(_t(s, '启用状态', 'Active status')),
                    onChanged: (value) => setState(() => _isActive = value),
                  ),
                if (_formError != null) ...[
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      _formError!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.danger),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _submitting ? null : () => Navigator.of(context).pop(),
          child: Text(_t(s, '取消', 'Cancel')),
        ),
        FilledButton(
          onPressed: _submitting ? null : _submit,
          child: _submitting
              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : Text(_isEdit ? _t(s, '保存', 'Save') : _t(s, '创建', 'Create')),
        ),
      ],
    );
  }

  void _clearFieldError(String field) {
    if (!_fieldErrors.containsKey(field)) return;
    setState(() {
      _fieldErrors = {..._fieldErrors}..remove(field);
    });
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final payload = <String, dynamic>{
      'username': _usernameController.text.trim(),
      'name': _nameController.text.trim(),
      'student_id': _normalizeText(_studentIdController.text),
      'phone': _normalizeText(_phoneController.text),
      'department': _departmentController.text.trim(),
      'class_name': _classController.text.trim(),
      'role': _role,
      'is_active': _isActive,
    };
    if (!_isEdit) {
      payload['password'] = _passwordController.text.trim();
    }
    setState(() {
      _submitting = true;
      _formError = null;
      _fieldErrors = const <String, String>{};
    });

    try {
      if (_isEdit) {
        await _service.updateMember(widget.member!.id, payload);
      } else {
        await _service.createMember(payload);
      }
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (error) {
      if (!mounted) return;
      final parsed = _parseValidationErrors(error, context.strings);
      setState(() {
        _fieldErrors = parsed.fieldErrors;
        _formError = parsed.message;
      });
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }
}

class _MemberImportDialog extends ConsumerStatefulWidget {
  const _MemberImportDialog();

  @override
  ConsumerState<_MemberImportDialog> createState() => _MemberImportDialogState();
}

class _MemberImportDialogState extends ConsumerState<_MemberImportDialog> {
  MemberImportTemplate? _template;
  MemberImportPreview? _preview;
  XFile? _selectedFile;
  bool _skipDuplicates = true;
  bool _loadingTemplate = true;
  bool _downloadingTemplate = false;
  bool _importing = false;
  String? _errorMessage;

  MembersCommandService get _service => ref.read(membersCommandProvider);

  @override
  void initState() {
    super.initState();
    _loadTemplate();
  }

  Future<void> _loadTemplate() async {
    final template = await _service.getImportTemplate();
    if (!mounted) return;
    setState(() {
      _template = template;
      _loadingTemplate = false;
    });
  }

  Future<void> _downloadTemplate() async {
    final template = _template;
    if (template == null) return;

    final location = await getSaveLocation(
      suggestedName: template.filename,
      acceptedTypeGroups: const [
        XTypeGroup(label: 'Excel/CSV', extensions: ['xlsx', 'xls', 'csv']),
      ],
    );
    if (!mounted || location == null) return;

    setState(() => _downloadingTemplate = true);
    try {
      final downloaded = await _service.downloadImportTemplate();
      final targetPath = location.path.endsWith('.xlsx') ||
              location.path.endsWith('.xls') ||
              location.path.endsWith('.csv')
          ? location.path
          : '${location.path}\\${downloaded.filename}';
      await File(targetPath).writeAsBytes(downloaded.bytes, flush: true);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _t(
              context.strings,
              '模板已保存到：$targetPath',
              'Template saved to $targetPath',
            ),
          ),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      setState(() => _errorMessage = _readableError(error, context.strings));
    } finally {
      if (mounted) {
        setState(() => _downloadingTemplate = false);
      }
    }
  }

  Future<void> _pickFile() async {
    final file = await openFile(
      acceptedTypeGroups: const [
        XTypeGroup(label: 'Excel/CSV', extensions: ['xlsx', 'xls', 'csv']),
      ],
    );
    if (!mounted || file == null) return;
    setState(() {
      _selectedFile = file;
      _preview = null;
      _errorMessage = null;
    });
  }

  Future<void> _submitImport() async {
    if (_selectedFile == null) return;
    setState(() {
      _importing = true;
      _errorMessage = null;
    });
    try {
      final preview = await _service.previewExcelImport(
        file: _selectedFile!,
        skipDuplicates: _skipDuplicates,
      );
      if (!mounted) return;
      setState(() => _preview = preview);
      if (preview.validRows == 0) {
        setState(() {
          _errorMessage = _t(
            context.strings,
            '导入文件未通过校验，请根据提示修正后重新上传。',
            'The import file did not pass validation. Please correct it and try again.',
          );
        });
        return;
      }

      final result = await _service.importExcel(
        file: _selectedFile!,
        skipDuplicates: _skipDuplicates,
      );
      if (!mounted) return;
      Navigator.of(context).pop(result);
    } catch (error) {
      if (!mounted) return;
      setState(() => _errorMessage = _readableError(error, context.strings));
    } finally {
      if (mounted) {
        setState(() => _importing = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    return AlertDialog(
      title: Text(_t(s, '批量导入成员', 'Import members')),
      content: SizedBox(
        width: 860,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _t(
                  s,
                  '请先下载模板文件，再按模板格式准备成员数据并上传导入。',
                  'Download the template file first, then prepare member data and upload it.',
                ),
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 16),
              if (_loadingTemplate)
                const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()))
              else
                GlassPanel(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              _t(s, '模板信息', 'Template info'),
                              style: Theme.of(context).textTheme.titleSmall,
                            ),
                          ),
                          OutlinedButton.icon(
                            onPressed: _downloadingTemplate ? null : _downloadTemplate,
                            icon: _downloadingTemplate
                                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                                : const Icon(Icons.download_rounded),
                            label: Text(_t(s, '下载模板', 'Download template')),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text('${_t(s, '文件名', 'Filename')}: ${_template?.filename ?? '--'}'),
                      Text(
                        '${_t(s, '支持格式', 'Supported formats')}: '
                        '${(_template?.supportedFileTypes ?? const ['.xlsx', '.xls', '.csv']).join(' / ')}',
                      ),
                      Text(
                        '${_t(s, '大小限制', 'Size limit')}: ${_template?.maxFileSizeMb ?? 10} MB',
                      ),
                      if ((_template?.columns.isNotEmpty ?? false)) ...[
                        const SizedBox(height: 8),
                        Text(_t(s, '字段', 'Fields'), style: Theme.of(context).textTheme.bodySmall),
                        const SizedBox(height: 6),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: _template!.columns
                              .map(
                                (column) => _StatusChip(
                                  label: '${column.name}${column.required ? '*' : ''}',
                                  color: column.required ? AppColors.accent : AppColors.textSecondary,
                                ),
                              )
                              .toList(growable: false),
                        ),
                      ],
                    ],
                  ),
                ),
              const SizedBox(height: 16),
              GlassPanel(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _selectedFile == null
                          ? _t(s, '未选择导入文件', 'No file selected')
                          : _t(
                              s,
                              '已选择：${_selectedFile!.name}',
                              'Selected: ${_selectedFile!.name}',
                            ),
                    ),
                    const SizedBox(height: 12),
                    CheckboxListTile(
                      value: _skipDuplicates,
                      contentPadding: EdgeInsets.zero,
                      title: Text(_t(s, '跳过重复成员', 'Skip duplicates')),
                      subtitle: Text(_t(s, '去重规则由后端决定，前端只传递开关。', 'Duplicate handling is decided by the backend.')),
                      onChanged: _importing ? null : (value) => setState(() => _skipDuplicates = value ?? true),
                    ),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        OutlinedButton.icon(
                          onPressed: _importing ? null : _pickFile,
                          icon: const Icon(Icons.attach_file_rounded),
                          label: Text(_t(s, '选择文件', 'Choose file')),
                        ),
                        FilledButton.icon(
                          onPressed: (_selectedFile == null || _importing) ? null : _submitImport,
                          icon: _importing
                              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                              : const Icon(Icons.cloud_upload_outlined),
                          label: Text(_t(s, '开始导入', 'Import now')),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              if (_errorMessage != null) ...[
                const SizedBox(height: 16),
                Text(
                  _errorMessage!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.danger),
                ),
              ],
              if (_preview != null) ...[
                const SizedBox(height: 16),
                GlassPanel(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_t(s, '校验结果', 'Validation result'), style: Theme.of(context).textTheme.titleSmall),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _StatusChip(
                            label: _t(s, '总行数：${_preview!.totalRows}', 'Rows: ${_preview!.totalRows}'),
                            color: AppColors.accent,
                          ),
                          _StatusChip(
                            label: _t(s, '有效：${_preview!.validRows}', 'Valid: ${_preview!.validRows}'),
                            color: AppColors.success,
                          ),
                          _StatusChip(
                            label: _t(s, '无效：${_preview!.invalidRows}', 'Invalid: ${_preview!.invalidRows}'),
                            color: AppColors.danger,
                          ),
                          _StatusChip(
                            label: _t(s, '空行：${_preview!.emptyRows}', 'Empty: ${_preview!.emptyRows}'),
                            color: AppColors.textSecondary,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _importing ? null : () => Navigator.of(context).pop(),
          child: Text(_t(s, '关闭', 'Close')),
        ),
      ],
    );
  }
}
class _PasswordDialog extends StatefulWidget {
  const _PasswordDialog({required this.requireOldPassword});

  final bool requireOldPassword;

  @override
  State<_PasswordDialog> createState() => _PasswordDialogState();
}

class _PasswordDialogState extends State<_PasswordDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _oldPasswordController;
  late final TextEditingController _newPasswordController;

  @override
  void initState() {
    super.initState();
    _oldPasswordController = TextEditingController();
    _newPasswordController = TextEditingController();
  }

  @override
  void dispose() {
    _oldPasswordController.dispose();
    _newPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    return AlertDialog(
      title: Text(_t(s, '修改密码', 'Change password')),
      content: SizedBox(
        width: 420,
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (widget.requireOldPassword) ...[
                TextFormField(
                  controller: _oldPasswordController,
                  obscureText: true,
                  decoration: InputDecoration(labelText: _t(s, '旧密码', 'Current password')),
                  validator: (value) => (value?.trim().isEmpty ?? true) ? _t(s, '请输入旧密码', 'Enter the current password') : null,
                ),
                const SizedBox(height: 12),
              ],
              TextFormField(
                controller: _newPasswordController,
                obscureText: true,
                decoration: InputDecoration(labelText: _t(s, '新密码', 'New password')),
                validator: (value) => (value?.trim().length ?? 0) < 6 ? _t(s, '密码至少 6 位', 'Password must be at least 6 characters') : null,
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(_t(s, '取消', 'Cancel'))),
        FilledButton(
          onPressed: () {
            if (!_formKey.currentState!.validate()) return;
            Navigator.of(context).pop(
              _PasswordValue(
                oldPassword: _normalizeText(_oldPasswordController.text),
                newPassword: _newPasswordController.text.trim(),
              ),
            );
          },
          child: Text(_t(s, '提交', 'Submit')),
        ),
      ],
    );
  }
}

class _PasswordValue {
  const _PasswordValue({required this.oldPassword, required this.newPassword});

  final String? oldPassword;
  final String newPassword;
}

List<DropdownMenuItem<String?>> _roleFilterItems(AppStrings s) {
  return [
    DropdownMenuItem<String?>(value: null, child: Text(_t(s, '全部角色', 'All roles'))),
    ..._roleItems(s).map((item) => DropdownMenuItem<String?>(value: item.value, child: item.child)),
  ];
}

List<DropdownMenuItem<String>> _roleItems(AppStrings s) {
  return [
    DropdownMenuItem<String>(value: 'admin', child: Text(_t(s, '管理员', 'Admin'))),
    DropdownMenuItem<String>(value: 'group_leader', child: Text(_t(s, '组长', 'Group leader'))),
    DropdownMenuItem<String>(value: 'member', child: Text(_t(s, '成员', 'Member'))),
    DropdownMenuItem<String>(value: 'guest', child: Text(_t(s, '访客', 'Guest'))),
  ];
}

String _roleLabel(AppStrings s, String? role) {
  switch (role) {
    case 'admin':
      return _t(s, '管理员', 'Admin');
    case 'group_leader':
      return _t(s, '组长', 'Group leader');
    case 'guest':
      return _t(s, '访客', 'Guest');
    default:
      return _t(s, '成员', 'Member');
  }
}

String _memberName(MemberItem member) {
  final name = member.name?.trim();
  return (name != null && name.isNotEmpty) ? name : member.username;
}

String _formatDate(String? raw) {
  if (raw == null || raw.trim().isEmpty) return '--';
  try {
    final dt = DateTime.parse(raw).toLocal();
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
  } catch (_) {
    return raw;
  }
}

List<int> _pageWindow(int currentPage, int totalPages) {
  if (totalPages <= 1) return const [1];
  final safeTotal = totalPages < 1 ? 1 : totalPages;
  final start = (currentPage - 1).clamp(1, safeTotal);
  final end = (start + 2).clamp(1, safeTotal);
  final adjustedStart = (end - 2).clamp(1, safeTotal);
  return [for (int page = adjustedStart; page <= end; page++) page];
}

class _ParsedFormError {
  const _ParsedFormError({
    required this.message,
    required this.fieldErrors,
  });

  final String message;
  final Map<String, String> fieldErrors;
}

_ParsedFormError _parseValidationErrors(Object error, AppStrings s) {
  if (error is! DioException) {
    return _ParsedFormError(
      message: _readableError(error, s),
      fieldErrors: const <String, String>{},
    );
  }

  final data = error.response?.data;
  if (data is! Map) {
    return _ParsedFormError(
      message: _readableError(error, s),
      fieldErrors: const <String, String>{},
    );
  }

  final map = Map<String, dynamic>.from(data);
  final fieldErrors = <String, String>{};

  final details = map['details'];
  if (details is Map) {
    final detailMap = Map<String, dynamic>.from(details);
    final rawFieldErrors = detailMap['field_errors'];
    if (rawFieldErrors is Map) {
      for (final entry in rawFieldErrors.entries) {
        final key = entry.key.toString().trim();
        final value = entry.value?.toString().trim();
        if (key.isNotEmpty && value != null && value.isNotEmpty) {
          fieldErrors[key] = _normalizeValidationMessage(value);
        }
      }
    }
  }

  final errors = map['errors'];
  if (errors is List) {
    for (final item in errors) {
      if (item is! Map) continue;
      final itemMap = Map<String, dynamic>.from(item);
      final field = itemMap['field']?.toString().trim();
      final message = itemMap['msg']?.toString().trim();
      if (field != null && field.isNotEmpty && message != null && message.isNotEmpty) {
        fieldErrors.putIfAbsent(field, () => _normalizeValidationMessage(message));
      }
    }
  }

  final detail = map['detail'];
  if (detail is List) {
    for (final item in detail) {
      if (item is! Map) continue;
      final itemMap = Map<String, dynamic>.from(item);
      final message = itemMap['msg']?.toString().trim();
      final loc = itemMap['loc'];
      String? field;
      if (loc is List && loc.isNotEmpty) {
        field = loc.last?.toString();
      }
      if (field != null && field.isNotEmpty && message != null && message.isNotEmpty) {
        fieldErrors.putIfAbsent(field, () => _normalizeValidationMessage(message));
      }
    }
  }

  final message = map['message']?.toString().trim();
  return _ParsedFormError(
    message: (message != null && message.isNotEmpty)
        ? message
        : _readableError(error, s),
    fieldErrors: fieldErrors,
  );
}

String _normalizeValidationMessage(String message) {
  final trimmed = message.trim();
  if (trimmed.startsWith('Value error,')) {
    return trimmed.replaceFirst('Value error,', '').trim();
  }
  return trimmed;
}

String _readableError(Object error, AppStrings s) {
  if (error is DioException) {
    final statusCode = error.response?.statusCode;
    final data = error.response?.data;
    if (statusCode == 401) {
      return _t(s, '登录状态已失效，请重新登录后再试。', 'Your session has expired. Please sign in again.');
    }
    if (statusCode == 403) {
      return _t(s, '当前账号没有执行该操作的权限。', 'Your account does not have permission to perform this action.');
    }
    if (data is Map<String, dynamic>) {
      final detail = data['detail'] as String? ?? data['message'] as String?;
      if (detail == 'Not authenticated') {
        return _t(s, '登录状态已失效，请重新登录后再试。', 'Your session has expired. Please sign in again.');
      }
      return detail ?? error.message ?? _t(s, '操作失败', 'Operation failed');
    }
    if (data is Map) {
      final map = Map<String, dynamic>.from(data);
      final detail = map['detail'] as String? ?? map['message'] as String?;
      if (detail == 'Not authenticated') {
        return _t(s, '登录状态已失效，请重新登录后再试。', 'Your session has expired. Please sign in again.');
      }
      return detail ?? error.message ?? _t(s, '操作失败', 'Operation failed');
    }
    if (error.message == 'Not authenticated') {
      return _t(s, '登录状态已失效，请重新登录后再试。', 'Your session has expired. Please sign in again.');
    }
    return error.message ?? _t(s, '操作失败', 'Operation failed');
  }
  final message = error.toString().replaceFirst('Exception: ', '').trim();
  return message.isEmpty ? _t(s, '操作失败', 'Operation failed') : message;
}

String? _normalizeText(String? value) {
  final trimmed = value?.trim();
  return (trimmed == null || trimmed.isEmpty) ? null : trimmed;
}

String _t(AppStrings s, String zh, String en) => s.isZh ? zh : en;

int? _asInt(Object? value) {
  if (value is int) return value;
  if (value is String) return int.tryParse(value);
  return null;
}

Widget _twoColumn(Widget left, Widget right) {
  return Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Expanded(child: left),
      const SizedBox(width: 12),
      Expanded(child: right),
    ],
  );
}



