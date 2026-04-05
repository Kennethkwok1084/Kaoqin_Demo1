import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_selector/file_selector.dart';

import '../../core/localization/app_strings.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/app_metric_card.dart';
import '../../shared/widgets/desktop_page.dart';
import '../../shared/widgets/glass_panel.dart';
import 'models/task_models.dart';
import 'providers/task_provider.dart';

enum _TaskSegment { all, pending, inProgress, completed }
enum _TaskRowAction { details, edit, start, complete, cancel }

class TasksScreen extends ConsumerStatefulWidget {
  const TasksScreen({super.key});

  @override
  ConsumerState<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends ConsumerState<TasksScreen> {
  late final TextEditingController _searchController;
  late final TextEditingController _memberIdController;
  TaskWorkspaceType _workspaceType = TaskWorkspaceType.repair;
  _TaskSegment _segment = _TaskSegment.all;
  int? _busyTaskId;
  final Set<int> _selectedTaskIds = <int>{};

  bool get _isRepair => _workspaceType == TaskWorkspaceType.repair;

  @override
  void initState() {
    super.initState();
    final params = ref.read(taskListParamsProvider);
    _workspaceType = params.type;
    _segment = _segmentFromStatus(params.status);
    _searchController = TextEditingController(text: params.search ?? '');
    _memberIdController = TextEditingController(
      text: params.memberId?.toString() ?? '',
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    _memberIdController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final params = ref.watch(taskListParamsProvider);
    final tasksAsync = ref.watch(taskListProvider);
    final statsAsync = ref.watch(taskStatsProvider);
    final actions = <Widget>[
      OutlinedButton.icon(
        onPressed: _refreshWorkspace,
        icon: const Icon(Icons.refresh_rounded),
        label: Text(s.refresh),
      ),
    ];

    if (_isRepair) {
      actions.addAll([
        const SizedBox(width: 12),
        OutlinedButton.icon(
          onPressed: _openRepairImportDialog,
          icon: const Icon(Icons.upload_file_rounded),
          label: Text(_text(s, zh: '导入工单', en: 'Import orders')),
        ),
        const SizedBox(width: 12),
        OutlinedButton.icon(
          onPressed: _selectedTaskIds.isEmpty ? null : _confirmBatchDelete,
          icon: const Icon(Icons.delete_sweep_rounded),
          label: Text(_text(s, zh: '批量删除', en: 'Batch delete')),
        ),
        const SizedBox(width: 12),
        FilledButton.icon(
          onPressed: _openCreateRepairDialog,
          icon: const Icon(Icons.add_rounded),
          label: Text(_text(s, zh: '新建报修', en: 'New repair')),
        ),
      ]);
    } else {
      actions.addAll([
        const SizedBox(width: 12),
        FilledButton.icon(
          onPressed: () => _showInfoSnackBar(_workspaceCreateHint(s, _workspaceType)),
          icon: const Icon(Icons.add_rounded),
          label: Text(_workspaceCreateLabel(s, _workspaceType)),
        ),
      ]);
    }

    return DesktopPage(
      title: s.tasksTitle,
      subtitle: _workspaceSubtitle(s, _workspaceType),
      actions: actions,
      children: [
        GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: TaskWorkspaceType.values
                    .map(
                      (type) => _SegmentChip(
                        label: _workspaceLabel(s, type),
                        selected: _workspaceType == type,
                        onTap: () => _changeWorkspace(type),
                      ),
                    )
                    .toList(growable: false),
              ),
              const SizedBox(height: 14),
              Text(_workspaceHint(s, _workspaceType), style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ),
        const SizedBox(height: 20),
        _buildStats(context, statsAsync),
        const SizedBox(height: 20),
        _buildFilters(context),
        const SizedBox(height: 20),
        GlassPanel(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 18),
          child: Column(
            children: [
              if (_isRepair && _selectedTaskIds.isNotEmpty) ...[
                _RepairBatchBar(
                  selectedCount: _selectedTaskIds.length,
                  onClear: () => setState(() => _selectedTaskIds.clear()),
                  onDelete: _confirmBatchDelete,
                ),
                const SizedBox(height: 10),
              ],
              _TaskHeaderRow(workspaceType: _workspaceType),
              const SizedBox(height: 10),
              tasksAsync.when(
                data: (data) => _TaskTable(
                  workspaceType: _workspaceType,
                  data: data,
                  currentPage: params.page,
                  busyTaskId: _busyTaskId,
                  selectedTaskIds: _selectedTaskIds,
                  onPageChanged: (page) => ref.read(taskListParamsProvider.notifier).setPage(page),
                  onToggleSelected: _toggleSelectedTask,
                  onOpenActions: _openTaskActions,
                ),
                loading: () => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 28),
                  child: DesktopStatusView(
                    icon: Icons.task_alt_rounded,
                    title: s.loadingTasks,
                    message: s.loadingTasksMsg,
                  ),
                ),
                error: (error, _) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 28),
                  child: DesktopStatusView(
                    icon: Icons.error_outline_rounded,
                    title: s.tasksUnavailable,
                    message: _readableError(error),
                    action: FilledButton(onPressed: _refreshWorkspace, child: Text(s.retry)),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildStats(BuildContext context, AsyncValue<TaskStats> statsAsync) {
    final s = context.strings;
    final stats = statsAsync.asData?.value ?? TaskStats.empty;
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 1180 ? 4 : constraints.maxWidth >= 720 ? 2 : 1;
        return GridView.count(
          crossAxisCount: columns,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          childAspectRatio: constraints.maxWidth >= 1320 ? 1.42 : 1.18,
          children: [
            AppMetricCard(
              title: _text(s, zh: '任务总数', en: 'Task total'),
              value: '${stats.total}',
              icon: Icons.task_alt_outlined,
              tint: AppColors.accent,
              caption: _workspaceStatsCaption(s, _workspaceType),
            ),
            AppMetricCard(
              title: _text(s, zh: '待处理', en: 'Pending'),
              value: '${stats.pending}',
              icon: Icons.pending_actions_outlined,
              tint: AppColors.warning,
              caption: _text(s, zh: '来自后端统计', en: 'From backend statistics'),
            ),
            AppMetricCard(
              title: _text(s, zh: '处理中', en: 'In progress'),
              value: '${stats.inProgress}',
              icon: Icons.autorenew_rounded,
              tint: AppColors.accent,
              caption: _text(s, zh: '来自后端统计', en: 'From backend statistics'),
            ),
            AppMetricCard(
              title: _text(s, zh: '已完成', en: 'Completed'),
              value: '${stats.completed}',
              icon: Icons.verified_rounded,
              tint: AppColors.success,
              caption: _text(s, zh: '来自后端统计', en: 'From backend statistics'),
            ),
          ],
        );
      },
    );
  }

  Widget _buildFilters(BuildContext context) {
    final s = context.strings;
    final disabledStatusText = _text(s, zh: '后续补充类型专属筛选项', en: 'Type-specific filters will follow');
    final batchText = _text(s, zh: '后续补充审核、批量操作与导入', en: 'Review, batch actions, and import will follow');
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_isRepair) ...[
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: _TaskSegment.values
                  .map(
                    (segment) => _SegmentChip(
                      label: _segmentLabel(s, segment),
                      selected: _segment == segment,
                      onTap: () => _changeSegment(segment),
                    ),
                  )
                  .toList(growable: false),
            ),
            const SizedBox(height: 16),
          ],
          LayoutBuilder(
            builder: (context, constraints) {
              const spacing = 12.0;
              final columns = constraints.maxWidth >= 1320 ? 5 : constraints.maxWidth >= 900 ? 3 : constraints.maxWidth >= 620 ? 2 : 1;
              final fieldWidth = columns == 1 ? constraints.maxWidth : (constraints.maxWidth - spacing * (columns - 1)) / columns;
              final fields = <(String, String)>[
                (_text(s, zh: '任务类型', en: 'Task type'), _workspaceLabel(s, _workspaceType)),
                (_text(s, zh: '数据来源', en: 'Data source'), _text(s, zh: '当前已接入真实后端列表', en: 'Live backend list connected')),
                (_text(s, zh: '状态筛选', en: 'Status filter'), _isRepair ? _segmentLabel(s, _segment) : disabledStatusText),
              ];
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
                          enabled: _isRepair,
                          onChanged: (_) => setState(() {}),
                          onSubmitted: (_) => _isRepair ? _applySearch() : null,
                          decoration: InputDecoration(
                            hintText: _isRepair ? s.applySearchHint : _text(s, zh: '当前任务类型暂不提供关键字筛选', en: 'Keyword filtering is not available yet'),
                            prefixIcon: const Icon(Icons.search_rounded),
                            suffixIcon: !_isRepair || _searchController.text.isEmpty ? null : IconButton(onPressed: _clearSearch, icon: const Icon(Icons.close_rounded)),
                          ),
                        ),
                      ),
                      SizedBox(
                        width: fieldWidth,
                        child: TextField(
                          controller: _memberIdController,
                          enabled: _isRepair,
                          keyboardType: TextInputType.number,
                          decoration: InputDecoration(
                            labelText: _text(s, zh: '成员 ID', en: 'Member ID'),
                            hintText: _isRepair
                                ? _text(s, zh: '按执行人成员 ID 筛选', en: 'Filter by assignee member ID')
                                : disabledStatusText,
                          ),
                        ),
                      ),
                      ...fields.map(
                        (item) => SizedBox(
                          width: fieldWidth,
                          child: TextField(
                            enabled: false,
                            decoration: InputDecoration(labelText: item.$1, hintText: item.$2),
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
                      OutlinedButton.icon(onPressed: _resetFilters, icon: const Icon(Icons.filter_alt_off_outlined), label: Text(s.resetFilters)),
                      FilledButton.icon(
                        onPressed: _isRepair ? _applySearch : null,
                        icon: const Icon(Icons.filter_alt_rounded),
                        label: Text(_text(s, zh: '应用筛选', en: 'Apply filters')),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(
                    _isRepair
                        ? _text(s, zh: '当前报修任务支持关键字、状态和执行人成员 ID 筛选。', en: 'Repair tasks currently support keyword, status, and assignee member ID filters.')
                        : batchText,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  void _refreshWorkspace() {
    ref.invalidate(taskListProvider);
    ref.invalidate(taskStatsProvider);
  }

  void _changeWorkspace(TaskWorkspaceType next) {
    if (_workspaceType == next) return;
    _searchController.clear();
    _memberIdController.clear();
    setState(() {
      _workspaceType = next;
      _segment = _TaskSegment.all;
      _selectedTaskIds.clear();
    });
    ref.read(taskListParamsProvider.notifier).updateParams(type: next, page: 1, status: null, search: null, memberId: null);
    _refreshWorkspace();
  }

  void _changeSegment(_TaskSegment next) {
    setState(() => _segment = next);
    ref.read(taskListParamsProvider.notifier).setStatus(_segmentStatus(next));
  }

  void _applySearch() {
    final memberId = int.tryParse(_memberIdController.text.trim());
    ref.read(taskListParamsProvider.notifier).setSearch(_searchController.text);
    ref.read(taskListParamsProvider.notifier).setMemberId(memberId);
    setState(() {});
  }

  void _clearSearch() {
    _searchController.clear();
    ref.read(taskListParamsProvider.notifier).setSearch(null);
    setState(() {});
  }

  void _toggleSelectedTask(int taskId, bool selected) {
    setState(() {
      if (selected) {
        _selectedTaskIds.add(taskId);
      } else {
        _selectedTaskIds.remove(taskId);
      }
    });
  }

  void _resetFilters() {
    _searchController.clear();
    _memberIdController.clear();
    setState(() => _segment = _TaskSegment.all);
    ref.read(taskListParamsProvider.notifier).resetFilters();
  }

  Future<void> _openCreateRepairDialog() async {
    final service = ref.read(taskCommandProvider);
    final result = await showDialog<bool>(
      context: context,
      useRootNavigator: true,
      builder: (_) => _RepairTaskFormDialog(
        title: _text(context.strings, zh: '新建报修任务', en: 'Create repair task'),
        onSubmit: (payload) => service.createRepairTask(payload),
      ),
    );
    if (result == true && mounted) {
      _refreshWorkspace();
      _showInfoSnackBar(_text(context.strings, zh: '报修任务已创建', en: 'Repair task created'));
    }
  }

  Future<void> _openEditRepairDialog(TaskItem task) async {
    final detail = await ref.read(
      taskDetailProvider(
        TaskDetailRef(taskId: task.id, type: TaskWorkspaceType.repair),
      ).future,
    );
    if (!mounted) {
      return;
    }
    final service = ref.read(taskCommandProvider);
    final result = await showDialog<bool>(
      context: context,
      useRootNavigator: true,
      builder: (_) => _RepairTaskFormDialog(
        title: _text(context.strings, zh: '编辑报修任务', en: 'Edit repair task'),
        task: task,
        detail: detail,
        onSubmit: (payload) => service.updateRepairTask(task.id, payload),
      ),
    );
    if (result == true && mounted) {
      _refreshWorkspace();
      ref.invalidate(taskDetailProvider(TaskDetailRef(taskId: task.id, type: TaskWorkspaceType.repair)));
      _showInfoSnackBar(_text(context.strings, zh: '报修任务已更新', en: 'Repair task updated'));
    }
  }

  Future<void> _openRepairImportDialog() async {
    final service = ref.read(taskCommandProvider);
    final result = await showDialog<RepairImportResult>(
      context: context,
      useRootNavigator: true,
      builder: (_) => _RepairImportDialog(service: service),
    );
    if (result != null && mounted) {
      _refreshWorkspace();
      _showInfoSnackBar(
        _text(
          context.strings,
          zh: '导入完成：成功 ${result.successfulImports} 条，失败 ${result.failedImports} 条，跳过 ${result.skippedDuplicates} 条',
          en: 'Import finished: ${result.successfulImports} success, ${result.failedImports} failed, ${result.skippedDuplicates} skipped',
        ),
      );
    }
  }

  Future<void> _confirmBatchDelete() async {
    if (_selectedTaskIds.isEmpty) {
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      useRootNavigator: true,
      builder: (dialogContext) => AlertDialog(
        title: Text(_text(context.strings, zh: '批量删除报修任务', en: 'Batch delete repair tasks')),
        content: Text(
          _text(
            context.strings,
            zh: '将删除已选中的 ${_selectedTaskIds.length} 条报修任务。该操作不可撤销。',
            en: 'This will delete ${_selectedTaskIds.length} selected repair tasks.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text(_text(context.strings, zh: '取消', en: 'Cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(_text(context.strings, zh: '确认删除', en: 'Delete')),
          ),
        ],
      ),
    );
    if (confirmed != true) {
      return;
    }

    final service = ref.read(taskCommandProvider);
    try {
      final result = await service.batchDeleteRepairTasks(_selectedTaskIds.toList(growable: false));
      if (!mounted) {
        return;
      }
      setState(() => _selectedTaskIds.clear());
      _refreshWorkspace();
      _showInfoSnackBar(
        _text(
          context.strings,
          zh: '已删除 ${result['deleted_count'] ?? 0} 条报修任务',
          en: 'Deleted ${result['deleted_count'] ?? 0} repair tasks',
        ),
      );
    } catch (error) {
      if (mounted) {
        _showErrorSnackBar(_readableError(error));
      }
    }
  }

  Future<void> _openTaskActions(TaskItem task) async {
    final action = await showDialog<_TaskRowAction>(
      context: context,
      useRootNavigator: true,
      builder: (_) => _TaskActionDialog(task: task, workspaceType: _workspaceType),
    );
    if (!mounted || action == null) return;

    switch (action) {
      case _TaskRowAction.details:
        await showDialog<void>(
          context: context,
          useRootNavigator: true,
          builder: (_) => _TaskDetailDialog(detailRef: TaskDetailRef(taskId: task.id, type: _workspaceType)),
        );
        return;
      case _TaskRowAction.edit:
        await _openEditRepairDialog(task);
        return;
      case _TaskRowAction.start:
        await _runRepairTaskCommand(task.id, _text(context.strings, zh: '任务已开始处理', en: 'Task started'), (service) => service.startTask(task.id));
        return;
      case _TaskRowAction.complete:
        await _completeTask(task);
        return;
      case _TaskRowAction.cancel:
        await _cancelTask(task);
        return;
    }
  }

  Future<void> _completeTask(TaskItem task) async {
    final s = context.strings;
    final text = await _showTextInputDialog(
      title: _text(s, zh: '标记完成', en: 'Complete task'),
      hintText: _text(s, zh: '实际工时（小时，可选）', en: 'Actual hours (optional)'),
    );
    if (text == null) return;
    final value = text.trim().isEmpty ? null : double.tryParse(text.trim());
    if (text.trim().isNotEmpty && value == null) {
      _showErrorSnackBar(_text(s, zh: '请输入有效的数字', en: 'Enter a valid number'));
      return;
    }
    await _runRepairTaskCommand(task.id, _text(s, zh: '任务已标记完成', en: 'Task completed'), (service) => service.completeTask(task.id, actualHours: value));
  }

  Future<void> _cancelTask(TaskItem task) async {
    final s = context.strings;
    final text = await _showTextInputDialog(
      title: _text(s, zh: '取消任务', en: 'Cancel task'),
      hintText: _text(s, zh: '取消原因（可选）', en: 'Cancellation reason (optional)'),
    );
    if (text == null) return;
    await _runRepairTaskCommand(task.id, _text(s, zh: '任务已取消', en: 'Task cancelled'), (service) => service.cancelTask(task.id, reason: text));
  }

  Future<void> _runRepairTaskCommand(int taskId, String successMessage, Future<void> Function(TaskCommandService service) command) async {
    final service = ref.read(taskCommandProvider);
    setState(() => _busyTaskId = taskId);
    try {
      await command(service);
      ref.invalidate(taskListProvider);
      ref.invalidate(taskStatsProvider);
      ref.invalidate(taskDetailProvider(TaskDetailRef(taskId: taskId, type: TaskWorkspaceType.repair)));
      if (mounted) _showInfoSnackBar(successMessage);
    } catch (error) {
      if (mounted) _showErrorSnackBar(_readableError(error));
    } finally {
      if (mounted) setState(() => _busyTaskId = null);
    }
  }

  Future<String?> _showTextInputDialog({required String title, required String hintText}) async {
    final s = context.strings;
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      useRootNavigator: true,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: TextField(controller: controller, autofocus: true, decoration: InputDecoration(hintText: hintText)),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(), child: Text(_text(s, zh: '关闭', en: 'Close'))),
          FilledButton(onPressed: () => Navigator.of(dialogContext).pop(controller.text), child: Text(_text(s, zh: '提交', en: 'Submit'))),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  void _showInfoSnackBar(String message) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));

  void _showErrorSnackBar(String message) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message), backgroundColor: AppColors.danger));

  String _readableError(Object error) {
    final message = error.toString().replaceFirst('Exception: ', '').trim();
    return message.isEmpty ? _text(context.strings, zh: '操作失败', en: 'Operation failed') : message;
  }
}

class _SegmentChip extends StatelessWidget {
  const _SegmentChip({required this.label, required this.selected, required this.onTap});
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      decoration: BoxDecoration(
        color: selected ? Colors.white : Colors.transparent,
        borderRadius: BorderRadius.circular(14),
        boxShadow: selected ? const [BoxShadow(color: Color(0x140F172A), blurRadius: 18, offset: Offset(0, 8))] : null,
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          child: Text(label, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: selected ? AppColors.textPrimary : AppColors.textSecondary, fontWeight: FontWeight.w700)),
        ),
      ),
    );
  }
}

class _TaskHeaderRow extends StatelessWidget {
  const _TaskHeaderRow({required this.workspaceType});
  final TaskWorkspaceType workspaceType;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final style = Theme.of(context).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w700, letterSpacing: 0.3);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(18)),
      child: Row(
        children: [
          Expanded(flex: 4, child: Text(s.taskContent, style: style)),
          Expanded(flex: 2, child: Text(workspaceType == TaskWorkspaceType.repair ? s.ownerAndLocation : _text(s, zh: '负责人 / 对象', en: 'Owner / target'), style: style)),
          Expanded(flex: 2, child: Text(workspaceType == TaskWorkspaceType.repair ? s.timeline : _text(s, zh: '开始 / 结束', en: 'Start / end'), style: style)),
          Expanded(flex: 2, child: Text(s.statusPriority, style: style)),
          const SizedBox(width: 56),
        ],
      ),
    );
  }
}

class _TaskTable extends StatelessWidget {
  const _TaskTable({required this.workspaceType, required this.data, required this.currentPage, required this.busyTaskId, required this.selectedTaskIds, required this.onPageChanged, required this.onToggleSelected, required this.onOpenActions});
  final TaskWorkspaceType workspaceType;
  final PaginatedData<TaskItem> data;
  final int currentPage;
  final int? busyTaskId;
  final Set<int> selectedTaskIds;
  final ValueChanged<int> onPageChanged;
  final void Function(int taskId, bool selected) onToggleSelected;
  final ValueChanged<TaskItem> onOpenActions;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    if (data.items.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 28),
        child: DesktopStatusView(icon: Icons.inbox_outlined, title: s.noTasks, message: _text(s, zh: '当前筛选条件下暂无任务记录。', en: 'No task records match the current filters.')),
      );
    }
    return Column(
      children: [
        ListView.separated(
          itemCount: data.items.length,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (context, index) => _TaskRow(
            workspaceType: workspaceType,
            task: data.items[index],
            busy: busyTaskId == data.items[index].id,
            selected: selectedTaskIds.contains(data.items[index].id),
            onToggleSelected: (selected) => onToggleSelected(data.items[index].id, selected),
            onOpenActions: () => onOpenActions(data.items[index]),
          ),
        ),
        const SizedBox(height: 18),
        _PaginationBar(total: data.total, currentPage: currentPage, totalPages: data.pages, onPageChanged: onPageChanged),
      ],
    );
  }
}

class _TaskRow extends StatelessWidget {
  const _TaskRow({required this.workspaceType, required this.task, required this.busy, required this.selected, required this.onToggleSelected, required this.onOpenActions});
  final TaskWorkspaceType workspaceType;
  final TaskItem task;
  final bool busy;
  final bool selected;
  final ValueChanged<bool> onToggleSelected;
  final VoidCallback onOpenActions;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final owner = workspaceType == TaskWorkspaceType.repair ? (task.assigneeName ?? task.memberName ?? s.unassigned) : (task.memberName ?? task.assigneeName ?? s.unassigned);
    final target = switch (workspaceType) {
      TaskWorkspaceType.repair => task.location ?? task.contactPerson ?? s.noLocation,
      TaskWorkspaceType.monitoring => task.monitoringType ?? task.location ?? s.notSet,
      TaskWorkspaceType.assistance => task.assistedDepartment ?? task.assistedPerson ?? s.notSet,
    };
    final timeTop = workspaceType == TaskWorkspaceType.repair ? _deadlineText(s, task) : _timeRangeText(s, task.startTime, task.endTime);
    final timeBottom = task.workMinutes == null ? s.createdAtLabel(_formatDate(s, task.createdAt)) : _text(s, zh: '工时 ${task.workMinutes} 分钟', en: '${task.workMinutes} min');
    final tag = switch (workspaceType) {
      TaskWorkspaceType.repair => _text(s, zh: '报修', en: 'Repair'),
      TaskWorkspaceType.monitoring => task.monitoringType ?? _text(s, zh: '监控', en: 'Monitoring'),
      TaskWorkspaceType.assistance => _text(s, zh: '协助', en: 'Assistance'),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.86), borderRadius: BorderRadius.circular(20), border: Border.all(color: AppColors.border)),
      child: Row(
        children: [
          if (workspaceType == TaskWorkspaceType.repair) ...[
            Checkbox(
              value: selected,
              onChanged: (value) => onToggleSelected(value ?? false),
            ),
            const SizedBox(width: 6),
          ],
          Expanded(
            flex: 4,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    _Badge(label: tag, color: AppColors.accent),
                    const SizedBox(width: 8),
                    Expanded(child: Text(task.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.titleMedium)),
                  ],
                ),
                const SizedBox(height: 8),
                Text(task.description ?? s.noDescription, maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            flex: 2,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(owner, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 6),
                Text(target, style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            flex: 2,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(timeTop, style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 6),
                Text(timeBottom, style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            flex: 2,
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _Badge(label: _statusLabel(s, task.status), color: _statusColor(task.status)),
                _Badge(label: _priorityLabel(s, task.priority), color: _priorityColor(task.priority)),
              ],
            ),
          ),
          SizedBox(
            width: 56,
            child: busy
                ? const Center(child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)))
                : IconButton(
                    onPressed: onOpenActions,
                    icon: const Icon(Icons.more_horiz_rounded),
                    style: IconButton.styleFrom(backgroundColor: AppColors.surfaceStrong, foregroundColor: AppColors.textSecondary),
                  ),
          ),
        ],
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.label, required this.color});
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(999)),
      child: Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: color, fontWeight: FontWeight.w700)),
    );
  }
}

class _RepairBatchBar extends StatelessWidget {
  const _RepairBatchBar({
    required this.selectedCount,
    required this.onClear,
    required this.onDelete,
  });

  final int selectedCount;
  final VoidCallback onClear;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.surfaceStrong,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              '已选择 $selectedCount 条报修任务',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
          TextButton(onPressed: onClear, child: const Text('清空选择')),
          const SizedBox(width: 8),
          FilledButton.icon(
            onPressed: onDelete,
            icon: const Icon(Icons.delete_outline_rounded),
            label: const Text('批量删除'),
          ),
        ],
      ),
    );
  }
}

class _PaginationBar extends StatelessWidget {
  const _PaginationBar({required this.total, required this.currentPage, required this.totalPages, required this.onPageChanged});
  final int total;
  final int currentPage;
  final int totalPages;
  final ValueChanged<int> onPageChanged;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final pages = _pageWindow(currentPage, totalPages);
    return Row(
      children: [
        Text(s.totalRecords(total), style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary)),
        const Spacer(),
        TextButton(onPressed: currentPage > 1 ? () => onPageChanged(currentPage - 1) : null, child: Text(s.previousPage)),
        ...pages.map((page) => Padding(
              padding: const EdgeInsets.only(left: 8),
              child: FilledButton.tonal(
                onPressed: currentPage == page ? null : () => onPageChanged(page),
                style: FilledButton.styleFrom(backgroundColor: currentPage == page ? AppColors.accent : AppColors.surfaceStrong, foregroundColor: currentPage == page ? Colors.white : AppColors.textPrimary),
                child: Text('$page'),
              ),
            )),
        const SizedBox(width: 8),
        TextButton(onPressed: currentPage < totalPages ? () => onPageChanged(currentPage + 1) : null, child: Text(s.nextPage)),
      ],
    );
  }
}

class _TaskActionDialog extends StatelessWidget {
  const _TaskActionDialog({required this.task, required this.workspaceType});
  final TaskItem task;
  final TaskWorkspaceType workspaceType;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final actions = <Widget>[
      _TaskActionButton(label: s.viewDetails, onPressed: () => Navigator.of(context).pop(_TaskRowAction.details)),
    ];
    if (workspaceType == TaskWorkspaceType.repair) {
      actions.add(
        _TaskActionButton(
          label: _text(s, zh: '编辑任务', en: 'Edit task'),
          onPressed: () => Navigator.of(context).pop(_TaskRowAction.edit),
        ),
      );
      if (task.status == 'pending') {
        actions.add(_TaskActionButton(label: _text(s, zh: '开始处理', en: 'Start task'), onPressed: () => Navigator.of(context).pop(_TaskRowAction.start)));
      }
      if (task.status == 'pending' || task.status == 'in_progress') {
        actions.add(_TaskActionButton(label: _text(s, zh: '标记完成', en: 'Complete task'), onPressed: () => Navigator.of(context).pop(_TaskRowAction.complete)));
      }
      if (task.status != 'completed' && task.status != 'cancelled') {
        actions.add(_TaskActionButton(label: _text(s, zh: '取消任务', en: 'Cancel task'), danger: true, onPressed: () => Navigator.of(context).pop(_TaskRowAction.cancel)));
      }
    }
    return AlertDialog(
      title: Text(task.title),
      contentPadding: const EdgeInsets.fromLTRB(24, 20, 24, 8),
      content: SizedBox(width: 320, child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: actions)),
      actions: [TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(_text(s, zh: '关闭', en: 'Close')))],
    );
  }
}

class _TaskActionButton extends StatelessWidget {
  const _TaskActionButton({required this.label, required this.onPressed, this.danger = false});
  final String label;
  final VoidCallback onPressed;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: OutlinedButton(
        onPressed: onPressed,
        style: OutlinedButton.styleFrom(
          alignment: Alignment.centerLeft,
          foregroundColor: danger ? AppColors.danger : AppColors.textPrimary,
          side: BorderSide(color: danger ? AppColors.danger.withValues(alpha: 0.25) : AppColors.borderStrong),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        ),
        child: Text(label),
      ),
    );
  }
}

class _TaskDetailDialog extends ConsumerWidget {
  const _TaskDetailDialog({required this.detailRef});
  final TaskDetailRef detailRef;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.strings;
    final detailAsync = ref.watch(taskDetailProvider(detailRef));
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 40, vertical: 32),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 820, maxHeight: 720),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: detailAsync.when(
            data: (detail) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(_text(s, zh: '任务详情', en: 'Task details'), style: Theme.of(context).textTheme.headlineSmall),
                          const SizedBox(height: 6),
                          Text(detail.title, style: Theme.of(context).textTheme.titleMedium),
                        ],
                      ),
                    ),
                    TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(_text(s, zh: '关闭', en: 'Close'))),
                  ],
                ),
                const SizedBox(height: 20),
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Wrap(
                          spacing: 10,
                          runSpacing: 10,
                          children: [
                            _Badge(label: _statusLabel(s, detail.status), color: _statusColor(detail.status)),
                            _Badge(label: _priorityLabel(s, detail.priority), color: _priorityColor(detail.priority)),
                            if ((detail.taskType ?? '').isNotEmpty) _Badge(label: detail.taskType!, color: AppColors.accent),
                          ],
                        ),
                        const SizedBox(height: 20),
                        _DetailGrid(children: [
                          _DetailItem(label: _text(s, zh: '任务编号', en: 'Task number'), value: detail.taskId),
                          _DetailItem(label: s.owner, value: detail.memberName ?? s.unassigned),
                          _DetailItem(label: _text(s, zh: '上报人', en: 'Reporter'), value: detail.reporterName ?? s.notSet),
                          _DetailItem(label: _text(s, zh: '联系方式', en: 'Contact'), value: detail.reporterContact ?? s.notSet),
                          _DetailItem(label: s.location, value: detail.location ?? s.noLocation),
                          _DetailItem(label: _text(s, zh: '分类', en: 'Category'), value: detail.category ?? s.notSet),
                          _DetailItem(label: _text(s, zh: '任务类型', en: 'Task type'), value: detail.taskType ?? s.notSet),
                          _DetailItem(label: _text(s, zh: '工时（分钟）', en: 'Work minutes'), value: _minutesText(detail.workMinutes, s)),
                          _DetailItem(label: _text(s, zh: '基础工时', en: 'Base work minutes'), value: _minutesText(detail.baseWorkMinutes, s)),
                          _DetailItem(label: _text(s, zh: '评分', en: 'Rating'), value: detail.rating?.toString() ?? s.notSet),
                        ]),
                        const SizedBox(height: 18),
                        _DetailSection(title: s.taskContent, child: Text((detail.description ?? '').trim().isEmpty ? s.noDescription : detail.description!, style: Theme.of(context).textTheme.bodyMedium)),
                        const SizedBox(height: 18),
                        _DetailSection(
                          title: _text(s, zh: '时间信息', en: 'Timeline'),
                          child: _DetailGrid(children: [
                            _DetailItem(label: s.created, value: _formatDate(s, detail.createdAt)),
                            _DetailItem(label: _text(s, zh: '报修时间', en: 'Reported at'), value: _formatDate(s, detail.reportTime)),
                            _DetailItem(label: _text(s, zh: '响应时间', en: 'Responded at'), value: _formatDate(s, detail.responseTime)),
                            _DetailItem(label: s.completed, value: _formatDate(s, detail.completionTime)),
                          ]),
                        ),
                        if (detail.memberStudentId != null ||
                            detail.isOverdueResponse != null ||
                            detail.isOverdueCompletion != null ||
                            detail.isPositiveReview != null ||
                            detail.isNegativeReview != null) ...[
                          const SizedBox(height: 18),
                          _DetailSection(
                            title: _text(s, zh: '执行信息', en: 'Execution info'),
                            child: _DetailGrid(children: [
                              if (detail.memberStudentId != null)
                                _DetailItem(label: _text(s, zh: '执行人学号', en: 'Member student ID'), value: detail.memberStudentId!),
                              _DetailItem(label: _text(s, zh: '响应是否超时', en: 'Response overdue'), value: detail.isOverdueResponse == true ? '是' : '否'),
                              _DetailItem(label: _text(s, zh: '完成是否超时', en: 'Completion overdue'), value: detail.isOverdueCompletion == true ? '是' : '否'),
                              if (detail.isPositiveReview != null)
                                _DetailItem(
                                  label: _text(s, zh: '是否正向评价', en: 'Positive review'),
                                  value: detail.isPositiveReview == true ? '是' : '否',
                                ),
                              if (detail.isNegativeReview != null)
                                _DetailItem(
                                  label: _text(s, zh: '是否负向评价', en: 'Negative review'),
                                  value: detail.isNegativeReview == true ? '是' : '否',
                                ),
                            ]),
                          ),
                        ],
                        if (detail.tags.isNotEmpty) ...[
                          const SizedBox(height: 18),
                          _DetailSection(
                            title: _text(s, zh: '标签', en: 'Tags'),
                            child: Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: detail.tags.map((tag) => _Badge(label: tag.name, color: AppColors.accent)).toList(),
                            ),
                          ),
                        ],
                        if (detail.feedback != null && detail.feedback!.trim().isNotEmpty) ...[
                          const SizedBox(height: 18),
                          _DetailSection(
                            title: _text(s, zh: '反馈', en: 'Feedback'),
                            child: Text(detail.feedback!),
                          ),
                        ],
                        if (detail.workHourBreakdown.isNotEmpty) ...[
                          const SizedBox(height: 18),
                          _DetailSection(
                            title: _text(s, zh: '工时明细', en: 'Work-hour breakdown'),
                            child: Wrap(
                              spacing: 10,
                              runSpacing: 10,
                              children: detail.workHourBreakdown.entries
                                  .map(
                                    (entry) => Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                                      decoration: BoxDecoration(
                                        color: AppColors.background,
                                        borderRadius: BorderRadius.circular(14),
                                      ),
                                      child: Text('${entry.key}: ${entry.value}'),
                                    ),
                                  )
                                  .toList(),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ],
            ),
            loading: () => DesktopStatusView(icon: Icons.hourglass_top_rounded, title: _text(s, zh: '任务详情', en: 'Task details'), message: s.loadingTasksMsg),
            error: (error, _) => DesktopStatusView(
              icon: Icons.error_outline_rounded,
              title: _text(s, zh: '无法获取任务详情', en: 'Task details are unavailable'),
              message: error.toString(),
              action: FilledButton(onPressed: () => ref.invalidate(taskDetailProvider(detailRef)), child: Text(s.retry)),
            ),
          ),
        ),
      ),
    );
  }
}

class _DetailSection extends StatelessWidget {
  const _DetailSection({required this.title, required this.child});
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
      const SizedBox(height: 10),
      child,
    ]);
  }
}

class _DetailGrid extends StatelessWidget {
  const _DetailGrid({required this.children});
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Wrap(spacing: 14, runSpacing: 14, children: children.map((child) => SizedBox(width: 230, child: child)).toList());
  }
}

class _DetailItem extends StatelessWidget {
  const _DetailItem({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(18), border: Border.all(color: AppColors.border)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Text(value, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700)),
      ]),
    );
  }
}

class _RepairTaskFormDialog extends StatefulWidget {
  const _RepairTaskFormDialog({
    required this.title,
    required this.onSubmit,
    this.task,
    this.detail,
  });

  final String title;
  final TaskItem? task;
  final TaskDetailItem? detail;
  final Future<Map<String, dynamic>> Function(Map<String, dynamic> payload) onSubmit;

  @override
  State<_RepairTaskFormDialog> createState() => _RepairTaskFormDialogState();
}

class _RepairTaskFormDialogState extends State<_RepairTaskFormDialog> {
  late final TextEditingController _titleController;
  late final TextEditingController _descriptionController;
  late final TextEditingController _locationController;
  late final TextEditingController _reporterNameController;
  late final TextEditingController _reporterContactController;
  late final TextEditingController _assignedToController;
  late final TextEditingController _completionNoteController;
  String _priority = 'medium';
  bool _submitting = false;
  String? _error;

  bool get _editing => widget.task != null;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.task?.title ?? '');
    _descriptionController = TextEditingController(
      text: widget.task?.description ?? widget.detail?.description ?? '',
    );
    _locationController = TextEditingController(text: widget.task?.location ?? widget.detail?.location ?? '');
    _reporterNameController = TextEditingController(text: widget.detail?.reporterName ?? '');
    _reporterContactController = TextEditingController(text: widget.detail?.reporterContact ?? '');
    _assignedToController = TextEditingController(text: widget.detail?.memberId?.toString() ?? '');
    _completionNoteController = TextEditingController();
    _priority = widget.detail?.priority ?? widget.task?.priority ?? 'medium';
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _locationController.dispose();
    _reporterNameController.dispose();
    _reporterContactController.dispose();
    _assignedToController.dispose();
    _completionNoteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 120, vertical: 60),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 760),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(widget.title, style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              Text(
                _editing ? '修改报修任务的基础信息和执行设置。' : '填写报修任务基础信息并提交到后端创建。',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 20),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  _dialogField(_titleController, '任务标题', width: 340),
                  _dialogField(_assignedToController, '执行人成员 ID', width: 160, keyboardType: TextInputType.number),
                  _dialogField(_locationController, '位置', width: 240, enabled: !_editing),
                  _dialogField(_reporterNameController, '上报人', width: 160, enabled: !_editing),
                  _dialogField(_reporterContactController, '联系方式', width: 200, enabled: !_editing),
                  SizedBox(
                    width: 160,
                    child: DropdownButtonFormField<String>(
                      initialValue: _priority,
                      decoration: const InputDecoration(labelText: '优先级'),
                      items: const [
                        DropdownMenuItem(value: 'low', child: Text('低')),
                        DropdownMenuItem(value: 'medium', child: Text('中')),
                        DropdownMenuItem(value: 'high', child: Text('高')),
                        DropdownMenuItem(value: 'urgent', child: Text('紧急')),
                      ],
                      onChanged: (value) => setState(() => _priority = value ?? 'medium'),
                    ),
                  ),
                  SizedBox(
                    width: 712,
                    child: TextField(
                      controller: _descriptionController,
                      maxLines: 4,
                      decoration: const InputDecoration(labelText: '任务描述'),
                    ),
                  ),
                  if (_editing)
                    SizedBox(
                      width: 712,
                      child: TextField(
                        controller: _completionNoteController,
                        maxLines: 3,
                        decoration: const InputDecoration(labelText: '补充备注'),
                      ),
                    ),
                ],
              ),
              if (_error != null) ...[
                const SizedBox(height: 14),
                Text(_error!, style: const TextStyle(color: AppColors.danger)),
              ],
              const SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: _submitting ? null : () => Navigator.of(context).pop(false),
                    child: Text(_text(s, zh: '取消', en: 'Cancel')),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    onPressed: _submitting ? null : _submit,
                    child: Text(_submitting ? '提交中...' : (_editing ? '保存' : '创建')),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _dialogField(
    TextEditingController controller,
    String label, {
    double width = 220,
    bool enabled = true,
    TextInputType? keyboardType,
  }) {
    return SizedBox(
      width: width,
      child: TextField(
        controller: controller,
        enabled: enabled,
        keyboardType: keyboardType,
        decoration: InputDecoration(labelText: label),
      ),
    );
  }

  Future<void> _submit() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      setState(() => _error = '任务标题不能为空');
      return;
    }

    final assignedTo = int.tryParse(_assignedToController.text.trim());
    final payload = <String, dynamic>{
      'title': title,
      if (_descriptionController.text.trim().isNotEmpty) 'description': _descriptionController.text.trim(),
      if (_editing) 'priority': _priority,
      if (assignedTo != null) 'assigned_to': assignedTo,
    };

    if (_editing) {
      if (_completionNoteController.text.trim().isNotEmpty) {
        payload['completion_note'] = _completionNoteController.text.trim();
      }
    } else {
      payload.addAll({
        'task_type': 'offline',
        'priority': _priority,
        if (_locationController.text.trim().isNotEmpty) 'location': _locationController.text.trim(),
        if (_reporterNameController.text.trim().isNotEmpty) 'reporter_name': _reporterNameController.text.trim(),
        if (_reporterContactController.text.trim().isNotEmpty) 'reporter_contact': _reporterContactController.text.trim(),
      });
    }

    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      await widget.onSubmit(payload);
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _submitting = false;
        _error = error.toString().replaceFirst('Exception: ', '');
      });
    }
  }
}

class _RepairImportDialog extends StatefulWidget {
  const _RepairImportDialog({required this.service});

  final TaskCommandService service;

  @override
  State<_RepairImportDialog> createState() => _RepairImportDialogState();
}

class _RepairImportDialogState extends State<_RepairImportDialog> {
  XFile? _selectedFile;
  RepairImportTemplate? _template;
  RepairImportPreview? _preview;
  String? _error;
  bool _skipDuplicates = true;
  bool _loadingTemplate = true;
  bool _previewing = false;
  bool _importing = false;

  @override
  void initState() {
    super.initState();
    _loadTemplate();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 100, vertical: 48),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 900, maxHeight: 760),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('导入维修工单', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              Text(
                '选择 Excel 或 CSV 文件后，系统将在导入前自动完成校验并返回处理结果。',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 20),
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      GlassPanel(
                        child: _loadingTemplate
                            ? const Padding(
                                padding: EdgeInsets.all(20),
                                child: CircularProgressIndicator(),
                              )
                            : Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('模板字段', style: Theme.of(context).textTheme.titleMedium),
                                  const SizedBox(height: 12),
                                  Wrap(
                                    spacing: 10,
                                    runSpacing: 10,
                                    children: (_template?.fields ?? const <RepairImportTemplateField>[])
                                        .map((field) => _Badge(
                                              label: field.required ? '${field.field}*' : field.field,
                                              color: field.required ? AppColors.accent : AppColors.textSecondary,
                                            ))
                                        .toList(),
                                  ),
                                ],
                              ),
                      ),
                      const SizedBox(height: 16),
                      GlassPanel(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(_selectedFile == null ? '未选择文件' : '已选择：${_selectedFile!.name}'),
                            const SizedBox(height: 12),
                            CheckboxListTile(
                              value: _skipDuplicates,
                              contentPadding: EdgeInsets.zero,
                              title: const Text('跳过重复工单'),
                              subtitle: const Text('去重规则由后端决定，前端只传递开关。'),
                              onChanged: (value) => setState(() => _skipDuplicates = value ?? true),
                            ),
                            const SizedBox(height: 12),
                            Wrap(
                              spacing: 12,
                              runSpacing: 12,
                              children: [
                                OutlinedButton.icon(
                                  onPressed: _pickFile,
                                  icon: const Icon(Icons.attach_file_rounded),
                                  label: const Text('选择文件'),
                                ),
                                FilledButton.icon(
                                  onPressed: _selectedFile == null || _previewing || _importing ? null : _runImport,
                                  icon: const Icon(Icons.upload_rounded),
                                  label: Text(_previewing || _importing ? '处理中...' : '开始导入'),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      if (_preview != null) ...[
                        const SizedBox(height: 16),
                        GlassPanel(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('校验结果', style: Theme.of(context).textTheme.titleMedium),
                              const SizedBox(height: 12),
                              Wrap(
                                spacing: 10,
                                runSpacing: 10,
                                children: [
                                  _Badge(label: '总行数 ${_preview!.totalRows}', color: AppColors.accent),
                                  _Badge(label: '有效 ${_preview!.validRows}', color: AppColors.success),
                                  _Badge(label: '无效 ${_preview!.invalidRows}', color: AppColors.danger),
                                  _Badge(label: '空行 ${_preview!.emptyRows}', color: AppColors.textSecondary),
                                ],
                              ),
                              if (_preview!.errors.isNotEmpty) ...[
                                const SizedBox(height: 12),
                                ..._preview!.errors.take(5).map(
                                  (error) => Padding(
                                    padding: const EdgeInsets.only(bottom: 6),
                                    child: Text(error, style: const TextStyle(color: AppColors.danger)),
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                      if (_error != null) ...[
                        const SizedBox(height: 12),
                        Text(_error!, style: const TextStyle(color: AppColors.danger)),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: _importing ? null : () => Navigator.of(context).pop(),
                  child: const Text('关闭'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _loadTemplate() async {
    try {
      final template = await widget.service.getRepairImportTemplate();
      if (!mounted) return;
      setState(() {
        _template = template;
        _loadingTemplate = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loadingTemplate = false;
        _error = error.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  Future<void> _pickFile() async {
    final file = await openFile(
      acceptedTypeGroups: const [
        XTypeGroup(
          label: 'repair import',
          extensions: ['xlsx', 'xls', 'csv'],
        ),
      ],
    );
    if (file == null || !mounted) {
      return;
    }
    setState(() {
      _selectedFile = file;
      _preview = null;
      _error = null;
    });
  }

  Future<void> _runImport() async {
    if (_selectedFile == null) return;
    setState(() {
      _previewing = true;
      _importing = true;
      _error = null;
    });
    try {
      final preview = await widget.service.previewRepairImport(
        _selectedFile!,
        skipDuplicates: _skipDuplicates,
      );
      if (!mounted) return;
      if (preview.invalidRows > 0 || preview.errors.isNotEmpty) {
        setState(() {
          _previewing = false;
          _importing = false;
          _preview = preview;
          _error = '文件校验未通过，请先修正后再导入。';
        });
        return;
      }

      setState(() {
        _previewing = false;
        _preview = preview;
      });
      final result = await widget.service.importRepairExcel(
        _selectedFile!,
        skipDuplicates: _skipDuplicates,
      );
      if (!mounted) return;
      Navigator.of(context).pop(result);
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _previewing = false;
        _importing = false;
        _error = error.toString().replaceFirst('Exception: ', '');
      });
    }
  }
}

String _workspaceLabel(AppStrings s, TaskWorkspaceType type) => switch (type) {
      TaskWorkspaceType.repair => _text(s, zh: '报修任务', en: 'Repair tasks'),
      TaskWorkspaceType.monitoring => _text(s, zh: '监控任务', en: 'Monitoring tasks'),
      TaskWorkspaceType.assistance => _text(s, zh: '协助任务', en: 'Assistance tasks'),
    };

String _workspaceSubtitle(AppStrings s, TaskWorkspaceType type) => switch (type) {
      TaskWorkspaceType.repair => _text(s, zh: '处理报修任务的流转、筛选、详情与状态操作。', en: 'Handle repair task workflow, filters, details, and status actions.'),
      TaskWorkspaceType.monitoring => _text(s, zh: '集中查看监控任务列表、时间信息与执行状态。', en: 'Review monitoring tasks, timelines, and execution status.'),
      TaskWorkspaceType.assistance => _text(s, zh: '集中查看协助任务列表、登记信息与审核状态。', en: 'Review assistance tasks, registrations, and review status.'),
    };

String _workspaceHint(AppStrings s, TaskWorkspaceType type) => switch (type) {
      TaskWorkspaceType.repair => _text(s, zh: '当前已接入真实列表、统计、详情和状态流转。', en: 'Live list, statistics, details, and status flow are connected.'),
      TaskWorkspaceType.monitoring => _text(s, zh: '当前已接入真实列表和统计；类型专属筛选与表单将后续补齐。', en: 'Live list and statistics are connected; type-specific filters and forms will follow.'),
      TaskWorkspaceType.assistance => _text(s, zh: '当前已接入真实列表和统计；审核、登记与批量能力将后续补齐。', en: 'Live list and statistics are connected; review, entry, and batch actions will follow.'),
    };

String _workspaceCreateLabel(AppStrings s, TaskWorkspaceType type) => switch (type) {
      TaskWorkspaceType.repair => _text(s, zh: '新建报修', en: 'New repair'),
      TaskWorkspaceType.monitoring => _text(s, zh: '新建监控', en: 'New monitoring'),
      TaskWorkspaceType.assistance => _text(s, zh: '登记协助', en: 'Log assistance'),
    };

String _workspaceCreateHint(AppStrings s, TaskWorkspaceType type) => switch (type) {
      TaskWorkspaceType.repair => _text(s, zh: '报修任务的新建表单将在下一阶段接入。', en: 'Repair creation form will be connected in the next phase.'),
      TaskWorkspaceType.monitoring => _text(s, zh: '监控任务的新建表单将在下一阶段接入。', en: 'Monitoring creation form will be connected in the next phase.'),
      TaskWorkspaceType.assistance => _text(s, zh: '协助任务的登记表单将在下一阶段接入。', en: 'Assistance entry form will be connected in the next phase.'),
    };

String _workspaceStatsCaption(AppStrings s, TaskWorkspaceType type) => switch (type) {
      TaskWorkspaceType.repair => _text(s, zh: '报修任务统计', en: 'Repair statistics'),
      TaskWorkspaceType.monitoring => _text(s, zh: '监控任务统计', en: 'Monitoring statistics'),
      TaskWorkspaceType.assistance => _text(s, zh: '协助任务统计', en: 'Assistance statistics'),
    };

_TaskSegment _segmentFromStatus(String? status) => switch (status) {
      'pending' => _TaskSegment.pending,
      'in_progress' => _TaskSegment.inProgress,
      'completed' => _TaskSegment.completed,
      _ => _TaskSegment.all,
    };

String? _segmentStatus(_TaskSegment segment) => switch (segment) {
      _TaskSegment.all => null,
      _TaskSegment.pending => 'pending',
      _TaskSegment.inProgress => 'in_progress',
      _TaskSegment.completed => 'completed',
    };

String _segmentLabel(AppStrings s, _TaskSegment segment) => switch (segment) {
      _TaskSegment.all => s.all,
      _TaskSegment.pending => s.pending,
      _TaskSegment.inProgress => s.processing,
      _TaskSegment.completed => s.completed,
    };

String _statusLabel(AppStrings s, String? status) => switch (status) {
      'pending' || 'pending_review' => s.pending,
      'in_progress' || 'processing' => s.processing,
      'completed' || 'approved' => s.completed,
      'cancelled' || 'rejected' => s.cancelled,
      _ => s.unknown,
    };

Color _statusColor(String? status) => switch (status) {
      'pending' || 'pending_review' => AppColors.warning,
      'in_progress' || 'processing' => AppColors.accent,
      'completed' || 'approved' => AppColors.success,
      'cancelled' || 'rejected' => AppColors.danger,
      _ => AppColors.textSecondary,
    };

String _priorityLabel(AppStrings s, String? priority) => switch (priority) {
      'urgent' => s.urgent,
      'high' => s.high,
      'medium' => s.medium,
      'low' => s.low,
      _ => s.regular,
    };

Color _priorityColor(String? priority) => switch (priority) {
      'urgent' => AppColors.danger,
      'high' => AppColors.warning,
      'medium' => const Color(0xFF635BFF),
      'low' => AppColors.success,
      _ => AppColors.textSecondary,
    };

List<int> _pageWindow(int currentPage, int totalPages) {
  if (totalPages <= 1) return const [1];
  final safeTotal = totalPages < 1 ? 1 : totalPages;
  final start = (currentPage - 1).clamp(1, safeTotal);
  final end = (start + 2).clamp(1, safeTotal);
  final adjustedStart = (end - 2).clamp(1, safeTotal);
  return [for (int page = adjustedStart; page <= end; page++) page];
}

String _formatDate(AppStrings s, String? rawDate) {
  if (rawDate == null || rawDate.isEmpty) return s.notSet;
  try {
    final dt = DateTime.parse(rawDate).toLocal();
    return '${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  } catch (_) {
    return rawDate;
  }
}

String _deadlineText(AppStrings s, TaskItem task) {
  if (task.dueDate == null || task.dueDate!.isEmpty) return s.notSet;
  try {
    final due = DateTime.parse(task.dueDate!).toLocal();
    final remaining = due.difference(DateTime.now());
    if (remaining.inHours <= 0) return s.arrived;
    if (remaining.inHours < 24) return s.remainingHours(remaining.inHours);
    return s.remainingDays(remaining.inDays);
  } catch (_) {
    return s.deadlineLabel(_formatDate(s, task.dueDate));
  }
}

String _timeRangeText(AppStrings s, String? start, String? end) {
  if ((start == null || start.isEmpty) && (end == null || end.isEmpty)) return s.notSet;
  final startText = _formatDate(s, start);
  final endText = _formatDate(s, end);
  return end == null || end.isEmpty ? startText : '$startText - $endText';
}

String _minutesText(int? minutes, AppStrings s) => minutes == null ? s.notSet : '$minutes';

String _text(AppStrings s, {required String zh, required String en}) => s.isZh ? zh : en;
