import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/app_strings.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/desktop_page.dart';
import '../../shared/widgets/glass_panel.dart';
import 'models/task_models.dart';
import 'providers/task_provider.dart';

enum _TaskSegment {
  all,
  pending,
  inProgress,
  completed,
}

enum _TaskRowAction {
  details,
  start,
  complete,
  cancel,
}

class TasksScreen extends ConsumerStatefulWidget {
  const TasksScreen({super.key});

  @override
  ConsumerState<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends ConsumerState<TasksScreen> {
  late final TextEditingController _searchController;
  _TaskSegment _segment = _TaskSegment.all;
  int? _busyTaskId;

  @override
  void initState() {
    super.initState();
    final params = ref.read(taskListParamsProvider);
    _searchController = TextEditingController(text: params.search ?? '');
    _segment = _segmentFromStatus(params.status);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final params = ref.watch(taskListParamsProvider);
    final tasksAsync = ref.watch(taskListProvider);

    return DesktopPage(
      title: s.tasksTitle,
      subtitle: s.tasksSubtitle,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            GlassPanel(
              padding: const EdgeInsets.all(6),
              radius: 20,
              backgroundColor: const Color(0xFFEFF2F8),
              borderColor: Colors.transparent,
              showShadow: false,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: _TaskSegment.values
                    .map(
                      (segment) => _SegmentChip(
                        label: _segmentLabel(s, segment),
                        selected: _segment == segment,
                        onTap: () => _changeSegment(segment),
                      ),
                    )
                    .toList(),
              ),
            ),
            const Spacer(),
            OutlinedButton.icon(
              onPressed: _resetFilters,
              icon: const Icon(Icons.filter_alt_off_outlined),
              label: Text(s.resetFilters),
            ),
            const SizedBox(width: 12),
            FilledButton.icon(
              onPressed: () => _showInfoSnackBar(
                _text(s, zh: '任务创建入口待接入', en: 'Task creation is not connected yet'),
              ),
              icon: const Icon(Icons.add_rounded),
              label: Text(s.createTask),
            ),
          ],
        ),
        const SizedBox(height: 20),
        Row(
          children: [
            SizedBox(
              width: 320,
              child: TextField(
                controller: _searchController,
                onChanged: (_) => setState(() {}),
                onSubmitted: (_) => _applySearch(),
                decoration: InputDecoration(
                  hintText: s.applySearchHint,
                  prefixIcon: const Icon(Icons.search_rounded),
                  suffixIcon: _searchController.text.isEmpty
                      ? null
                      : IconButton(
                          onPressed: _clearSearch,
                          icon: const Icon(Icons.close_rounded),
                        ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            OutlinedButton.icon(
              onPressed: _applySearch,
              icon: const Icon(Icons.arrow_forward_rounded),
              label: Text(s.applySearch),
            ),
            const SizedBox(width: 12),
            OutlinedButton.icon(
              onPressed: () => ref.invalidate(taskListProvider),
              icon: const Icon(Icons.refresh_rounded),
              label: Text(s.refresh),
            ),
          ],
        ),
        const SizedBox(height: 20),
        GlassPanel(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 18),
          child: Column(
            children: [
              const _TaskHeaderRow(),
              const SizedBox(height: 10),
              tasksAsync.when(
                data: (data) => _TaskTable(
                  data: data,
                  currentPage: params.page,
                  busyTaskId: _busyTaskId,
                  onPageChanged: (page) => ref.read(taskListParamsProvider.notifier).setPage(page),
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
                error: (err, stack) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 28),
                  child: DesktopStatusView(
                    icon: Icons.error_outline_rounded,
                    title: s.tasksUnavailable,
                    message: err.toString(),
                    action: FilledButton(
                      onPressed: () => ref.invalidate(taskListProvider),
                      child: Text(s.retry),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _changeSegment(_TaskSegment next) {
    setState(() {
      _segment = next;
    });
    ref.read(taskListParamsProvider.notifier).setStatus(_segmentStatus(next));
  }

  void _applySearch() {
    ref.read(taskListParamsProvider.notifier).setSearch(_searchController.text);
    setState(() {});
  }

  void _clearSearch() {
    _searchController.clear();
    ref.read(taskListParamsProvider.notifier).setSearch(null);
    setState(() {});
  }

  void _resetFilters() {
    _searchController.clear();
    setState(() {
      _segment = _TaskSegment.all;
    });
    ref.read(taskListParamsProvider.notifier).resetFilters();
  }

  Future<void> _handleTaskAction(TaskItem task, _TaskRowAction action) async {
    if (_busyTaskId != null) {
      _showInfoSnackBar(_text(context.strings, zh: '正在提交操作，请稍候。', en: 'Action in progress. Please wait.'));
      return;
    }

    switch (action) {
      case _TaskRowAction.details:
        return _openTaskDetails(task.id);
      case _TaskRowAction.start:
        return _runTaskCommand(
          task.id,
          successMessage: _text(context.strings, zh: '任务已开始处理', en: 'Task started'),
          command: (service) => service.startTask(task.id),
        );
      case _TaskRowAction.complete:
        return _completeTask(task);
      case _TaskRowAction.cancel:
        return _cancelTask(task);
    }
  }

  Future<void> _openTaskActions(TaskItem task) async {
    final action = await showDialog<_TaskRowAction>(
      context: context,
      useRootNavigator: true,
      builder: (_) => _TaskActionDialog(task: task),
    );

    if (!mounted || action == null) {
      return;
    }

    await _handleTaskAction(task, action);
  }

  Future<void> _openTaskDetails(int taskId) async {
    await showDialog<void>(
      context: context,
      useRootNavigator: true,
      builder: (_) => _TaskDetailDialog(taskId: taskId),
    );
  }

  Future<void> _completeTask(TaskItem task) async {
    final s = context.strings;
    final actualHoursText = await _showTextInputDialog(
      title: _text(s, zh: '标记完成', en: 'Complete task'),
      hintText: _text(s, zh: '实际工时（小时，可选）', en: 'Actual hours (optional)'),
    );
    if (actualHoursText == null) {
      return;
    }

    final trimmed = actualHoursText.trim();
    final actualHours = trimmed.isEmpty ? null : double.tryParse(trimmed);
    if (trimmed.isNotEmpty && actualHours == null) {
      _showErrorSnackBar(_text(s, zh: '请输入正确的数字', en: 'Enter a valid number'));
      return;
    }

    await _runTaskCommand(
      task.id,
      successMessage: _text(s, zh: '任务已完成', en: 'Task completed'),
      command: (service) => service.completeTask(task.id, actualHours: actualHours),
    );
  }

  Future<void> _cancelTask(TaskItem task) async {
    final s = context.strings;
    final reason = await _showTextInputDialog(
      title: _text(s, zh: '取消任务', en: 'Cancel task'),
      hintText: _text(s, zh: '取消原因（可选）', en: 'Cancellation reason (optional)'),
    );
    if (reason == null) {
      return;
    }

    await _runTaskCommand(
      task.id,
      successMessage: _text(s, zh: '任务已取消', en: 'Task cancelled'),
      command: (service) => service.cancelTask(task.id, reason: reason),
    );
  }

  Future<void> _runTaskCommand(
    int taskId, {
    required String successMessage,
    required Future<void> Function(TaskCommandService service) command,
  }) async {
    final service = ref.read(taskCommandProvider);
    setState(() {
      _busyTaskId = taskId;
    });

    try {
      await command(service);
      ref.invalidate(taskListProvider);
      ref.invalidate(taskDetailProvider(taskId));
      if (mounted) {
        _showInfoSnackBar(successMessage);
      }
    } catch (error) {
      if (mounted) {
        _showErrorSnackBar(_readableError(error));
      }
    } finally {
      if (mounted) {
        setState(() {
          _busyTaskId = null;
        });
      }
    }
  }

  Future<String?> _showTextInputDialog({
    required String title,
    required String hintText,
  }) async {
    final s = context.strings;
    final controller = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      useRootNavigator: true,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: InputDecoration(hintText: hintText),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: Text(_text(s, zh: '关闭', en: 'Close')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(controller.text),
            child: Text(_text(s, zh: '提交', en: 'Submit')),
          ),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  void _showInfoSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.danger,
      ),
    );
  }

  String _readableError(Object error) {
    final message = error.toString().replaceFirst('Exception: ', '').trim();
    if (message.isEmpty) {
      return _text(context.strings, zh: '操作失败', en: 'Operation failed');
    }
    return message;
  }
}

class _SegmentChip extends StatelessWidget {
  const _SegmentChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

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
        boxShadow: selected
            ? const [
                BoxShadow(
                  color: Color(0x140F172A),
                  blurRadius: 18,
                  offset: Offset(0, 8),
                ),
              ]
            : null,
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          child: Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: selected ? AppColors.textPrimary : AppColors.textSecondary,
                  fontWeight: FontWeight.w700,
                ),
          ),
        ),
      ),
    );
  }
}

class _TaskHeaderRow extends StatelessWidget {
  const _TaskHeaderRow();

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final style = Theme.of(context).textTheme.bodySmall?.copyWith(
          fontWeight: FontWeight.w700,
          letterSpacing: 0.3,
        );

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        children: [
          Expanded(flex: 4, child: Text(s.taskContent, style: style)),
          Expanded(flex: 2, child: Text(s.ownerAndLocation, style: style)),
          Expanded(flex: 2, child: Text(s.timeline, style: style)),
          Expanded(flex: 2, child: Text(s.statusPriority, style: style)),
          const SizedBox(width: 56),
        ],
      ),
    );
  }
}

class _TaskTable extends StatelessWidget {
  const _TaskTable({
    required this.data,
    required this.currentPage,
    required this.busyTaskId,
    required this.onPageChanged,
    required this.onOpenActions,
  });

  final PaginatedData<TaskItem> data;
  final int currentPage;
  final int? busyTaskId;
  final ValueChanged<int> onPageChanged;
  final ValueChanged<TaskItem> onOpenActions;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;

    if (data.items.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 28),
        child: DesktopStatusView(
          icon: Icons.inbox_outlined,
          title: s.noTasks,
          message: s.noTasksMsg,
        ),
      );
    }

    return Column(
      children: [
        ListView.separated(
          itemCount: data.items.length,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (context, index) {
            final task = data.items[index];
            return _TaskRow(
              task: task,
              busy: busyTaskId == task.id,
              onOpenActions: () => onOpenActions(task),
            );
          },
        ),
        const SizedBox(height: 18),
        _PaginationBar(
          total: data.total,
          currentPage: currentPage,
          totalPages: data.pages,
          onPageChanged: onPageChanged,
        ),
      ],
    );
  }
}

class _TaskRow extends StatelessWidget {
  const _TaskRow({
    required this.task,
    required this.busy,
    required this.onOpenActions,
  });

  final TaskItem task;
  final bool busy;
  final VoidCallback onOpenActions;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final statusColor = _statusColor(task.status);
    final priorityColor = _priorityColor(task.priority);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.86),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Expanded(
            flex: 4,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    _Badge(
                      label: _taskType(s, task),
                      color: AppColors.accent,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        task.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  task.description ?? s.noDescription,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            flex: 2,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  task.assigneeName ?? s.unassigned,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
                const SizedBox(height: 6),
                Text(
                  task.location ?? s.noLocation,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            flex: 2,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _deadlineText(s, task),
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 6),
                Text(
                  s.createdAtLabel(_formatDate(s, task.createdAt)),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
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
                _Badge(
                  label: _statusLabel(s, task.status),
                  color: statusColor,
                ),
                _Badge(
                  label: _priorityLabel(s, task.priority),
                  color: priorityColor,
                ),
              ],
            ),
          ),
          SizedBox(
            width: 56,
            child: busy
                ? const Center(
                    child: SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  )
                : IconButton(
                    onPressed: onOpenActions,
                    icon: const Icon(Icons.more_horiz_rounded),
                    style: IconButton.styleFrom(
                      backgroundColor: AppColors.surfaceStrong,
                      foregroundColor: AppColors.textSecondary,
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({
    required this.label,
    required this.color,
  });

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w700,
            ),
      ),
    );
  }
}

class _PaginationBar extends StatelessWidget {
  const _PaginationBar({
    required this.total,
    required this.currentPage,
    required this.totalPages,
    required this.onPageChanged,
  });

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
        Text(
          s.totalRecords(total),
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
        ),
        const Spacer(),
        TextButton(
          onPressed: currentPage > 1 ? () => onPageChanged(currentPage - 1) : null,
          child: Text(s.previousPage),
        ),
        ...pages.map(
          (page) => Padding(
            padding: const EdgeInsets.only(left: 8),
            child: FilledButton.tonal(
              onPressed: currentPage == page ? null : () => onPageChanged(page),
              style: FilledButton.styleFrom(
                backgroundColor: currentPage == page ? AppColors.accent : AppColors.surfaceStrong,
                foregroundColor: currentPage == page ? Colors.white : AppColors.textPrimary,
              ),
              child: Text('$page'),
            ),
          ),
        ),
        const SizedBox(width: 8),
        TextButton(
          onPressed: currentPage < totalPages ? () => onPageChanged(currentPage + 1) : null,
          child: Text(s.nextPage),
        ),
      ],
    );
  }
}

class _TaskActionDialog extends StatelessWidget {
  const _TaskActionDialog({required this.task});

  final TaskItem task;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final actions = <Widget>[
      _TaskActionButton(
        label: s.viewDetails,
        onPressed: () => Navigator.of(context).pop(_TaskRowAction.details),
      ),
    ];

    if (task.status == 'pending') {
      actions.add(
        _TaskActionButton(
          label: _text(s, zh: '开始处理', en: 'Start task'),
          onPressed: () => Navigator.of(context).pop(_TaskRowAction.start),
        ),
      );
    }

    if (task.status == 'pending' || task.status == 'in_progress') {
      actions.add(
        _TaskActionButton(
          label: _text(s, zh: '标记完成', en: 'Complete task'),
          onPressed: () => Navigator.of(context).pop(_TaskRowAction.complete),
        ),
      );
    }

    if (task.status != 'completed' && task.status != 'cancelled') {
      actions.add(
        _TaskActionButton(
          label: _text(s, zh: '取消任务', en: 'Cancel task'),
          danger: true,
          onPressed: () => Navigator.of(context).pop(_TaskRowAction.cancel),
        ),
      );
    }

    return AlertDialog(
      title: Text(task.title),
      contentPadding: const EdgeInsets.fromLTRB(24, 20, 24, 8),
      content: SizedBox(
        width: 320,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: actions,
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(_text(s, zh: '关闭', en: 'Close')),
        ),
      ],
    );
  }
}

class _TaskActionButton extends StatelessWidget {
  const _TaskActionButton({
    required this.label,
    required this.onPressed,
    this.danger = false,
  });

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
          side: BorderSide(
            color: danger ? AppColors.danger.withValues(alpha: 0.25) : AppColors.borderStrong,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        ),
        child: Text(label),
      ),
    );
  }
}

class _TaskDetailDialog extends ConsumerWidget {
  const _TaskDetailDialog({required this.taskId});

  final int taskId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.strings;
    final detailAsync = ref.watch(taskDetailProvider(taskId));

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
                          Text(
                            _text(s, zh: '任务详情', en: 'Task details'),
                            style: Theme.of(context).textTheme.headlineSmall,
                          ),
                          const SizedBox(height: 6),
                          Text(
                            detail.title,
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                        ],
                      ),
                    ),
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: Text(_text(s, zh: '关闭', en: 'Close')),
                    ),
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
                            _Badge(
                              label: _statusLabel(s, detail.status),
                              color: _statusColor(detail.status),
                            ),
                            _Badge(
                              label: _priorityLabel(s, detail.priority),
                              color: _priorityColor(detail.priority),
                            ),
                            if ((detail.taskType ?? '').isNotEmpty)
                              _Badge(
                                label: detail.taskType!,
                                color: const Color(0xFF635BFF),
                              ),
                          ],
                        ),
                        const SizedBox(height: 20),
                        _DetailGrid(
                          children: [
                            _DetailItem(
                              label: _text(s, zh: '任务编号', en: 'Task number'),
                              value: detail.taskId,
                            ),
                            _DetailItem(
                              label: s.owner,
                              value: detail.memberName ?? s.unassigned,
                            ),
                            _DetailItem(
                              label: _text(s, zh: '报修人', en: 'Reporter'),
                              value: detail.reporterName ?? s.notSet,
                            ),
                            _DetailItem(
                              label: _text(s, zh: '联系方式', en: 'Contact'),
                              value: detail.reporterContact ?? s.notSet,
                            ),
                            _DetailItem(
                              label: s.location,
                              value: detail.location ?? s.noLocation,
                            ),
                            _DetailItem(
                              label: _text(s, zh: '分类', en: 'Category'),
                              value: detail.category ?? s.notSet,
                            ),
                            _DetailItem(
                              label: _text(s, zh: '任务类型', en: 'Task type'),
                              value: detail.taskType ?? s.notSet,
                            ),
                            _DetailItem(
                              label: _text(s, zh: '工时（分钟）', en: 'Work minutes'),
                              value: _minutesText(detail.workMinutes, s),
                            ),
                            _DetailItem(
                              label: _text(s, zh: '基础工时', en: 'Base work minutes'),
                              value: _minutesText(detail.baseWorkMinutes, s),
                            ),
                            _DetailItem(
                              label: _text(s, zh: '评分', en: 'Rating'),
                              value: detail.rating?.toString() ?? s.notSet,
                            ),
                          ],
                        ),
                        const SizedBox(height: 18),
                        _DetailSection(
                          title: s.taskContent,
                          child: Text(
                            (detail.description ?? '').trim().isEmpty ? s.noDescription : detail.description!,
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ),
                        const SizedBox(height: 18),
                        _DetailSection(
                          title: _text(s, zh: '时间线', en: 'Timeline'),
                          child: _DetailGrid(
                            children: [
                              _DetailItem(
                                label: s.created,
                                value: _formatDate(s, detail.createdAt),
                              ),
                              _DetailItem(
                                label: _text(s, zh: '报修时间', en: 'Reported at'),
                                value: _formatDate(s, detail.reportTime),
                              ),
                              _DetailItem(
                                label: _text(s, zh: '响应时间', en: 'Responded at'),
                                value: _formatDate(s, detail.responseTime),
                              ),
                              _DetailItem(
                                label: s.completed,
                                value: _formatDate(s, detail.completionTime),
                              ),
                            ],
                          ),
                        ),
                        if (detail.tags.isNotEmpty) ...[
                          const SizedBox(height: 18),
                          _DetailSection(
                            title: _text(s, zh: '标签', en: 'Tags'),
                            child: Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: detail.tags
                                  .map((tag) => _Badge(label: tag.name, color: AppColors.accent))
                                  .toList(),
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
            loading: () => DesktopStatusView(
              icon: Icons.hourglass_top_rounded,
              title: _text(s, zh: '任务详情', en: 'Task details'),
              message: s.loadingTasksMsg,
            ),
            error: (error, stack) => DesktopStatusView(
              icon: Icons.error_outline_rounded,
              title: _text(s, zh: '未获取到任务详情', en: 'Task details are unavailable'),
              message: error.toString(),
              action: FilledButton(
                onPressed: () => ref.invalidate(taskDetailProvider(taskId)),
                child: Text(s.retry),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _DetailSection extends StatelessWidget {
  const _DetailSection({
    required this.title,
    required this.child,
  });

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w700,
              ),
        ),
        const SizedBox(height: 10),
        child,
      ],
    );
  }
}

class _DetailGrid extends StatelessWidget {
  const _DetailGrid({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 14,
      runSpacing: 14,
      children: children
          .map(
            (child) => SizedBox(
              width: 230,
              child: child,
            ),
          )
          .toList(),
    );
  }
}

class _DetailItem extends StatelessWidget {
  const _DetailItem({
    required this.label,
    required this.value,
  });

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            value.trim().isEmpty ? '--' : value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
        ],
      ),
    );
  }
}

_TaskSegment _segmentFromStatus(String? status) {
  switch (status) {
    case 'pending':
      return _TaskSegment.pending;
    case 'in_progress':
      return _TaskSegment.inProgress;
    case 'completed':
      return _TaskSegment.completed;
    default:
      return _TaskSegment.all;
  }
}

String? _segmentStatus(_TaskSegment segment) {
  switch (segment) {
    case _TaskSegment.all:
      return null;
    case _TaskSegment.pending:
      return 'pending';
    case _TaskSegment.inProgress:
      return 'in_progress';
    case _TaskSegment.completed:
      return 'completed';
  }
}

String _segmentLabel(AppStrings s, _TaskSegment segment) {
  switch (segment) {
    case _TaskSegment.all:
      return s.all;
    case _TaskSegment.pending:
      return s.pending;
    case _TaskSegment.inProgress:
      return s.processing;
    case _TaskSegment.completed:
      return s.completed;
  }
}

String _taskType(AppStrings s, TaskItem task) {
  if (task.contactPerson != null && task.contactPerson!.isNotEmpty) {
    return s.repairTag;
  }
  if (task.location != null && task.location!.isNotEmpty) {
    return s.fieldTag;
  }
  return s.genericTaskTag;
}

String _statusLabel(AppStrings s, String? status) {
  switch (status) {
    case 'pending':
      return s.pending;
    case 'in_progress':
      return s.processing;
    case 'completed':
      return s.completed;
    case 'cancelled':
      return s.cancelled;
    default:
      return s.unknown;
  }
}

Color _statusColor(String? status) {
  switch (status) {
    case 'pending':
      return AppColors.warning;
    case 'in_progress':
      return AppColors.accent;
    case 'completed':
      return AppColors.success;
    case 'cancelled':
      return AppColors.textSecondary;
    default:
      return const Color(0xFF635BFF);
  }
}

String _priorityLabel(AppStrings s, String? priority) {
  switch (priority) {
    case 'urgent':
      return s.urgent;
    case 'high':
      return s.high;
    case 'medium':
      return s.medium;
    case 'low':
      return s.low;
    default:
      return s.regular;
  }
}

Color _priorityColor(String? priority) {
  switch (priority) {
    case 'urgent':
      return AppColors.danger;
    case 'high':
      return AppColors.warning;
    case 'medium':
      return const Color(0xFF635BFF);
    case 'low':
      return AppColors.success;
    default:
      return AppColors.textSecondary;
  }
}

// ignore: unused_element
List<PopupMenuEntry<_TaskRowAction>> _taskMenuItems(AppStrings s, TaskItem task) {
  final items = <PopupMenuEntry<_TaskRowAction>>[
    PopupMenuItem<_TaskRowAction>(
      value: _TaskRowAction.details,
      child: Text(s.viewDetails),
    ),
  ];

  if (task.status == 'pending') {
    items.add(
      PopupMenuItem<_TaskRowAction>(
        value: _TaskRowAction.start,
        child: Text(_text(s, zh: '开始处理', en: 'Start task')),
      ),
    );
  }

  if (task.status == 'pending' || task.status == 'in_progress') {
    items.add(
      PopupMenuItem<_TaskRowAction>(
        value: _TaskRowAction.complete,
        child: Text(_text(s, zh: '标记完成', en: 'Complete task')),
      ),
    );
  }

  if (task.status != 'completed' && task.status != 'cancelled') {
    items.add(
      PopupMenuItem<_TaskRowAction>(
        value: _TaskRowAction.cancel,
        child: Text(_text(s, zh: '取消任务', en: 'Cancel task')),
      ),
    );
  }

  return items;
}

List<int> _pageWindow(int currentPage, int totalPages) {
  if (totalPages <= 1) {
    return const [1];
  }

  final safeTotal = totalPages < 1 ? 1 : totalPages;
  final start = (currentPage - 1).clamp(1, safeTotal);
  final end = (start + 2).clamp(1, safeTotal);
  final adjustedStart = (end - 2).clamp(1, safeTotal);

  return [
    for (int page = adjustedStart; page <= end; page++) page,
  ];
}

String _formatDate(AppStrings s, String? rawDate) {
  if (rawDate == null || rawDate.isEmpty) {
    return s.notSet;
  }

  try {
    final dt = DateTime.parse(rawDate).toLocal();
    return '${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} '
        '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  } catch (_) {
    return rawDate;
  }
}

String _deadlineText(AppStrings s, TaskItem task) {
  if (task.dueDate == null || task.dueDate!.isEmpty) {
    return s.notSet;
  }

  try {
    final due = DateTime.parse(task.dueDate!).toLocal();
    final remaining = due.difference(DateTime.now());
    if (remaining.inHours <= 0) {
      return s.arrived;
    }
    if (remaining.inHours < 24) {
      return s.remainingHours(remaining.inHours);
    }
    return s.remainingDays(remaining.inDays);
  } catch (_) {
    return s.deadlineLabel(_formatDate(s, task.dueDate));
  }
}

String _minutesText(int? minutes, AppStrings s) {
  if (minutes == null) {
    return s.notSet;
  }
  return '$minutes';
}

String _text(
  AppStrings s, {
  required String zh,
  required String en,
}) {
  return s.isZh ? zh : en;
}
