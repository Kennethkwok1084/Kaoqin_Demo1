import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/app_strings.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/desktop_page.dart';
import '../../shared/widgets/glass_panel.dart';
import 'models/dashboard_models.dart';
import 'providers/dashboard_provider.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.strings;
    final dashboardAsync = ref.watch(dashboardScreenProvider);

    return DesktopPage(
      title: s.dashboardTitle,
      subtitle: s.dashboardSubtitle,
      actions: [
        OutlinedButton.icon(
          onPressed: () => ref.invalidate(dashboardScreenProvider),
          icon: const Icon(Icons.refresh_rounded),
          label: Text(s.refresh),
        ),
      ],
      children: [
        dashboardAsync.when(
          data: (data) => _DashboardBody(data: data),
          loading: () => DesktopStatusView(
            icon: Icons.hourglass_top_rounded,
            title: s.loadingDashboard,
            message: s.loadingDashboardMsg,
          ),
          error: (err, stack) => DesktopStatusView(
            icon: Icons.error_outline_rounded,
            title: s.dashboardUnavailable,
            message: err.toString(),
            action: FilledButton(
              onPressed: () => ref.invalidate(dashboardScreenProvider),
              child: Text(s.retry),
            ),
          ),
        ),
      ],
    );
  }
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody({required this.data});

  final DashboardScreenData data;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final overview = data.overview;
    final metrics = overview.metrics;
    final trends = overview.trends;
    final primaryAlert = data.alerts.isNotEmpty ? data.alerts.first : null;

    return Column(
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            final width = constraints.maxWidth;
            final columns = width >= 1260 ? 4 : width >= 760 ? 2 : 1;
            final aspectRatio = columns == 4 ? 1.55 : columns == 2 ? 1.85 : 2.7;

            return GridView.count(
              crossAxisCount: columns,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 18,
              mainAxisSpacing: 18,
              childAspectRatio: aspectRatio,
              children: [
                _StatCard(
                  title: s.totalTasks,
                  value: '${metrics.totalTasks}',
                  unit: s.tasksSection,
                  accent: AppColors.accent,
                  background: AppColors.accentSoft,
                  icon: Icons.space_dashboard_outlined,
                  trend: _trendText(trends.totalTasksTrend),
                ),
                _StatCard(
                  title: s.pendingTasks,
                  value: '${metrics.pending}',
                  unit: s.tasksSection,
                  accent: const Color(0xFF5B64F6),
                  background: const Color(0xFFEDEBFF),
                  icon: Icons.inbox_outlined,
                  trend: _trendText(trends.pendingTrend),
                ),
                _StatCard(
                  title: s.weeklyWarnings,
                  value: '${data.alerts.length}',
                  unit: s.records,
                  accent: AppColors.warning,
                  background: const Color(0xFFFFF2DE),
                  icon: Icons.warning_amber_rounded,
                ),
                _StatCard(
                  title: s.monthlyCompleted,
                  value: '${metrics.completedThisMonth}',
                  unit: s.tasksSection,
                  accent: AppColors.success,
                  background: const Color(0xFFE6F7ED),
                  icon: Icons.check_circle_outline_rounded,
                  trend: _trendText(trends.completedTrend),
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 24),
        LayoutBuilder(
          builder: (context, constraints) {
            final wide = constraints.maxWidth >= 1140;
            final mainColumn = Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SectionHeader(
                  title: s.quickActions,
                  subtitle: s.quickActionsSubtitle,
                ),
                const SizedBox(height: 16),
                LayoutBuilder(
                  builder: (context, actionConstraints) {
                    final compact = actionConstraints.maxWidth < 840;
                    return GridView.count(
                      crossAxisCount: compact ? 1 : 3,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisSpacing: 16,
                      mainAxisSpacing: 16,
                      childAspectRatio: compact ? 3.6 : 1.45,
                      children: [
                        _ActionCard(
                          icon: Icons.add_task_rounded,
                          title: s.registerAssistTask,
                          description: s.registerAssistTaskDesc,
                          fill: AppColors.accent,
                          foreground: Colors.white,
                        ),
                        _ActionCard(
                          icon: Icons.description_outlined,
                          title: s.importOfflineOrder,
                          description: s.importOfflineOrderDesc,
                        ),
                        _ActionCard(
                          icon: Icons.assignment_turned_in_outlined,
                          title: s.claimPendingOrder,
                          description: s.claimPendingOrderDesc,
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 24),
                SectionHeader(
                  title: s.recentTasks,
                  subtitle: s.recentTasksSubtitle,
                ),
                const SizedBox(height: 16),
                GlassPanel(
                  padding: const EdgeInsets.fromLTRB(18, 18, 18, 12),
                  child: Column(
                    children: [
                      const _TaskTableHeader(),
                      const SizedBox(height: 8),
                      if (data.myTasks.isEmpty)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 28),
                          child: DesktopStatusView(
                            icon: Icons.inbox_outlined,
                            title: s.noTasks,
                            message: s.noTasksMsg,
                          ),
                        )
                      else
                        ...data.myTasks.map(
                          (task) => Padding(
                            padding: const EdgeInsets.only(bottom: 10),
                            child: _RecentTaskRow(task: task),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            );

            final sideColumn = Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SectionHeader(
                  title: s.rankingTitle,
                  subtitle: s.rankingSubtitle,
                ),
                const SizedBox(height: 16),
                GlassPanel(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (data.memberPerformance.isEmpty)
                        Text(
                          s.noTasksMsg,
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: AppColors.textSecondary,
                              ),
                        )
                      else
                        ...data.memberPerformance.asMap().entries.map(
                          (entry) => Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: _RankingRow(
                              item: entry.value,
                              rank: entry.key + 1,
                            ),
                          ),
                        ),
                      const SizedBox(height: 8),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton(
                          onPressed: () {},
                          child: Text(s.viewFullRanking),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                GlassPanel(
                  padding: EdgeInsets.zero,
                  backgroundColor: Colors.transparent,
                  borderColor: Colors.transparent,
                  showShadow: false,
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: _alertGradient(primaryAlert?.level),
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(28),
                      boxShadow: const [
                        BoxShadow(
                          color: Color(0x33007AFF),
                          blurRadius: 28,
                          offset: Offset(0, 16),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 34,
                              height: 34,
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.18),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: const Icon(
                                Icons.notifications_active_outlined,
                                color: Colors.white,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                primaryAlert?.title ?? s.systemNotice,
                                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                      color: Colors.white,
                                    ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Text(
                          _noticeMessage(context, data, primaryAlert),
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: Colors.white.withValues(alpha: 0.92),
                              ),
                        ),
                        const SizedBox(height: 18),
                        OutlinedButton(
                          onPressed: () {},
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.white,
                            side: BorderSide(color: Colors.white.withValues(alpha: 0.34)),
                          ),
                          child: Text(s.viewDetails),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            );

            if (wide) {
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(flex: 2, child: mainColumn),
                  const SizedBox(width: 24),
                  SizedBox(width: 320, child: sideColumn),
                ],
              );
            }

            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                mainColumn,
                const SizedBox(height: 24),
                sideColumn,
              ],
            );
          },
        ),
      ],
    );
  }

  static String _trendText(TrendData trend) {
    final sign = trend.direction == 'up' ? '+' : '-';
    return '$sign${trend.value.toStringAsFixed(1)}%';
  }

  static List<Color> _alertGradient(String? level) {
    switch (level) {
      case 'high':
        return const [Color(0xFFFF7A59), Color(0xFFFF453A)];
      case 'medium':
        return const [Color(0xFFFFB347), Color(0xFFFF9F0A)];
      default:
        return const [AppColors.accent, Color(0xFF5B64F6)];
    }
  }

  static String _noticeMessage(
    BuildContext context,
    DashboardScreenData data,
    DashboardAlertItem? alert,
  ) {
    final s = context.strings;
    if (alert != null && alert.message.trim().isNotEmpty) {
      return alert.message;
    }

    final info = data.overview.systemInfo;
    return '${s.systemNotice}: ${info.onlineUsers} online, ${info.systemUptime} uptime, last sync ${_formatDate(info.lastDataSync)}';
  }

  static String _formatDate(String? rawDate) {
    if (rawDate == null || rawDate.isEmpty) {
      return '--';
    }
    try {
      final dt = DateTime.parse(rawDate).toLocal();
      return '${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return rawDate;
    }
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.title,
    required this.value,
    required this.unit,
    required this.accent,
    required this.background,
    required this.icon,
    this.trend,
  });

  final String title;
  final String value;
  final String unit;
  final Color accent;
  final Color background;
  final IconData icon;
  final String? trend;

  @override
  Widget build(BuildContext context) {
    return GlassPanel(
      radius: 28,
      padding: const EdgeInsets.all(22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: background,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(icon, color: accent),
              ),
              const Spacer(),
              if (trend != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppColors.background,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    trend!,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ),
            ],
          ),
          const Spacer(),
          Text(
            title,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 13),
          ),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                value,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontSize: 30,
                      color: accent == AppColors.warning ? AppColors.danger : AppColors.textPrimary,
                    ),
              ),
              const SizedBox(width: 6),
              Padding(
                padding: const EdgeInsets.only(bottom: 3),
                child: Text(
                  unit,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({
    required this.icon,
    required this.title,
    required this.description,
    this.fill = AppColors.surfaceStrong,
    this.foreground = AppColors.textPrimary,
  });

  final IconData icon;
  final String title;
  final String description;
  final Color fill;
  final Color foreground;

  @override
  Widget build(BuildContext context) {
    return GlassPanel(
      backgroundColor: fill,
      borderColor: fill == AppColors.surfaceStrong ? AppColors.borderStrong : fill,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: foreground.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(icon, color: foreground),
          ),
          const SizedBox(height: 18),
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(color: foreground),
          ),
          const SizedBox(height: 8),
          Text(
            description,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: foreground.withValues(alpha: 0.78),
                ),
          ),
        ],
      ),
    );
  }
}

class _TaskTableHeader extends StatelessWidget {
  const _TaskTableHeader();

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final style = Theme.of(context).textTheme.bodySmall?.copyWith(
          fontWeight: FontWeight.w700,
          letterSpacing: 0.3,
        );

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        children: [
          Expanded(flex: 4, child: Text(s.workbenchTaskInfo, style: style)),
          Expanded(flex: 2, child: Text(s.location, style: style)),
          Expanded(flex: 2, child: Text(s.status, style: style)),
          Expanded(flex: 2, child: Text(s.timeline, style: style)),
          const SizedBox(width: 48),
        ],
      ),
    );
  }
}

class _RecentTaskRow extends StatelessWidget {
  const _RecentTaskRow({required this.task});

  final DashboardTaskSummaryItem task;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final statusColor = _statusColor(task.status);
    final tagColor = _priorityColor(task.priority);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.78),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Expanded(
            flex: 4,
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: tagColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    _priorityLabel(s, task.priority),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: tagColor,
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    task.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            flex: 2,
            child: Text(
              task.location.isEmpty ? s.noLocation : task.location,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          Expanded(
            flex: 2,
            child: Row(
              children: [
                Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    color: statusColor,
                    borderRadius: BorderRadius.circular(999),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  _statusLabel(s, task.status),
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
          Expanded(
            flex: 2,
            child: Text(
              _timelineText(s, task.dueDate),
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w600,
                  ),
            ),
          ),
          SizedBox(
            width: 48,
            child: IconButton(
              onPressed: () {},
              icon: const Icon(Icons.chevron_right_rounded),
              style: IconButton.styleFrom(
                backgroundColor: AppColors.accentSoft,
                foregroundColor: AppColors.accent,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RankingRow extends StatelessWidget {
  const _RankingRow({
    required this.item,
    required this.rank,
  });

  final DashboardMemberPerformanceItem item;
  final int rank;

  @override
  Widget build(BuildContext context) {
    final medals = <String>['🥇', '🥈', '🥉'];

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: rank == 1 ? AppColors.accentSoft : Colors.white.withValues(alpha: 0.52),
        borderRadius: BorderRadius.circular(18),
        border: rank == 1 ? Border.all(color: const Color(0x33007AFF)) : null,
      ),
      child: Row(
        children: [
          SizedBox(
            width: 28,
            child: Text(
              rank <= 3 ? medals[rank - 1] : '$rank',
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(width: 10),
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFFE1E5EF), Color(0xFFC7CEDA)],
              ),
              borderRadius: BorderRadius.circular(999),
            ),
            alignment: Alignment.center,
            child: Text(
              item.memberName.isNotEmpty ? item.memberName.substring(0, 1) : '?',
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              item.memberName,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: rank == 1 ? AppColors.accent : AppColors.textPrimary,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
          Text(
            '${(item.workHours / 60).toStringAsFixed(1)}h',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
        ],
      ),
    );
  }
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

String _timelineText(AppStrings s, String? dueDate) {
  if (dueDate == null || dueDate.isEmpty) {
    return s.notSet;
  }

  try {
    final due = DateTime.parse(dueDate).toLocal();
    final remaining = due.difference(DateTime.now());
    if (remaining.inHours <= 0) {
      return s.arrived;
    }
    if (remaining.inHours < 24) {
      return s.remainingHours(remaining.inHours);
    }
    return s.remainingDays(remaining.inDays);
  } catch (_) {
    return s.deadlineLabel(dueDate);
  }
}
