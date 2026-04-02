import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/app_strings.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/app_metric_card.dart';
import '../../shared/widgets/desktop_page.dart';
import '../../shared/widgets/glass_panel.dart';
import 'models/work_hour_models.dart';
import 'providers/work_hours_provider.dart';

class WorkHoursScreen extends ConsumerWidget {
  const WorkHoursScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.strings;
    final recordsAsync = ref.watch(workHoursListProvider);

    return DesktopPage(
      title: s.workHoursTitle,
      subtitle: s.workHoursSubtitle,
      actions: [
        OutlinedButton.icon(
          onPressed: () => ref.refresh(workHoursListProvider),
          icon: const Icon(Icons.refresh_rounded),
          label: Text(s.refresh),
        ),
      ],
      children: [
        recordsAsync.when(
          data: (records) => _WorkHoursBody(records: records),
          loading: () => DesktopStatusView(
            icon: Icons.schedule_rounded,
            title: s.loadingWorkHours,
            message: s.loadingWorkHoursMsg,
          ),
          error: (err, stack) => DesktopStatusView(
            icon: Icons.error_outline_rounded,
            title: s.workHoursUnavailable,
            message: err.toString(),
            action: FilledButton(
              onPressed: () => ref.refresh(workHoursListProvider),
              child: Text(s.retry),
            ),
          ),
        ),
      ],
    );
  }
}

class _WorkHoursBody extends StatelessWidget {
  const _WorkHoursBody({required this.records});

  final List<WorkHourRecord> records;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final currentListOnlyHint = s.isZh
        ? '顶部指标仅基于当前已加载的列表记录，不代表全局统计。'
        : 'The summary cards are based on the currently loaded records only, not a global total.';

    if (records.isEmpty) {
      return DesktopStatusView(
        icon: Icons.av_timer_outlined,
        title: s.noWorkHours,
        message: s.noWorkHoursMsg,
      );
    }

    final totalHours = records.fold<double>(
      0,
      (sum, record) => sum + (record.workHours ?? 0),
    );
    final manualCount = records.where((record) => record.source == 'manual').length;
    final ratedCount = records.where((record) => (record.rating ?? 0) > 0).length;

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
                AppMetricCard(
                  title: s.loggedHours,
                  value: totalHours.toStringAsFixed(1),
                  icon: Icons.timer_outlined,
                  tint: AppColors.accent,
                  caption: s.workHourEntries(records.length),
                ),
                AppMetricCard(
                  title: s.manualRecords,
                  value: '$manualCount',
                  icon: Icons.edit_note_rounded,
                  tint: AppColors.warning,
                  caption: s.handAdded,
                ),
                AppMetricCard(
                  title: s.ratedTasks,
                  value: '$ratedCount',
                  icon: Icons.grade_outlined,
                  tint: AppColors.success,
                  caption: s.qualitySignal,
                ),
                AppMetricCard(
                  title: s.membersInvolved,
                  value: '${records.map((record) => record.memberId).toSet().length}',
                  icon: Icons.people_outline_rounded,
                  tint: AppColors.textSecondary,
                  caption: s.uniqueContributors,
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 16),
        GlassPanel(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          radius: 20,
          child: Row(
            children: [
              const Icon(
                Icons.info_outline_rounded,
                color: AppColors.textSecondary,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  currentListOnlyHint,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        GlassPanel(
          child: Column(
            children: [
              const _WorkHourHeader(),
              const SizedBox(height: 8),
              for (final record in records) ...[
                _WorkHourRow(record: record),
                const SizedBox(height: 10),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _WorkHourHeader extends StatelessWidget {
  const _WorkHourHeader();

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final style = Theme.of(context).textTheme.bodySmall?.copyWith(
          fontWeight: FontWeight.w700,
          letterSpacing: 0.4,
        );

    return Row(
      children: [
        Expanded(flex: 3, child: Text(s.entry, style: style)),
        Expanded(flex: 2, child: Text(s.member, style: style)),
        Expanded(flex: 2, child: Text(s.date, style: style)),
        Expanded(flex: 2, child: Text(s.type, style: style)),
        Expanded(flex: 1, child: Text(s.hours, style: style)),
      ],
    );
  }
}

class _WorkHourRow extends StatelessWidget {
  const _WorkHourRow({required this.record});

  final WorkHourRecord record;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.74),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Expanded(
            flex: 3,
            child: Text(
              record.title ?? s.workHourRecordLabel(record.id),
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
          Expanded(
            flex: 2,
            child: Text(record.memberName ?? s.unknownMember),
          ),
          Expanded(
            flex: 2,
            child: Text(record.workDate ?? s.noDate),
          ),
          Expanded(
            flex: 2,
            child: Text(record.taskType ?? record.taskCategory ?? s.general),
          ),
          Expanded(
            flex: 1,
            child: Text(
              '+${(record.workHours ?? 0).toStringAsFixed(1)}h',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.success,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}
