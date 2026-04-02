import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/app_strings.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/app_metric_card.dart';
import '../../shared/widgets/desktop_page.dart';
import '../../shared/widgets/glass_panel.dart';
import 'models/report_models.dart';
import 'providers/reports_provider.dart';

class ReportsScreen extends ConsumerWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.strings;
    final overviewAsync = ref.watch(statisticsOverviewProvider);

    return DesktopPage(
      title: s.reportsTitle,
      subtitle: s.reportsSubtitle,
      actions: [
        OutlinedButton.icon(
          onPressed: () => ref.read(statisticsOverviewProvider.notifier).refresh(),
          icon: const Icon(Icons.refresh_rounded),
          label: Text(s.refresh),
        ),
      ],
      children: [
        overviewAsync.when(
          data: (data) => _ReportsBody(data: data),
          loading: () => DesktopStatusView(
            icon: Icons.insights_rounded,
            title: s.loadingReports,
            message: s.loadingReportsMsg,
          ),
          error: (err, stack) => DesktopStatusView(
            icon: Icons.error_outline_rounded,
            title: s.reportsUnavailable,
            message: err.toString(),
            action: FilledButton(
              onPressed: () => ref.read(statisticsOverviewProvider.notifier).refresh(),
              child: Text(s.retry),
            ),
          ),
        ),
      ],
    );
  }
}

class _ReportsBody extends StatelessWidget {
  const _ReportsBody({required this.data});

  final StatisticsOverview data;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            final wide = constraints.maxWidth >= 1100;
            return wide
                ? Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(child: _SummaryColumn(data: data)),
                      const SizedBox(width: 24),
                      SizedBox(
                        width: 340,
                        child: _InsightSidebar(data: data),
                      ),
                    ],
                  )
                : Column(
                    children: [
                      _SummaryColumn(data: data),
                      const SizedBox(height: 24),
                      _InsightSidebar(data: data),
                    ],
                  );
          },
        ),
      ],
    );
  }
}

class _SummaryColumn extends StatelessWidget {
  const _SummaryColumn({required this.data});

  final StatisticsOverview data;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;

    return Column(
      children: [
        _StatSection(
          title: s.attendance,
          subtitle: s.hoursLateRateRecords,
          cards: [
            AppMetricCard(
              title: s.totalHours,
              value: '${data.attendance.totalWorkHours} h',
              icon: Icons.schedule_rounded,
              tint: AppColors.accent,
            ),
            AppMetricCard(
              title: s.averageHours,
              value: '${data.attendance.avgWorkHours} h',
              icon: Icons.query_stats_rounded,
              tint: AppColors.success,
            ),
            AppMetricCard(
              title: s.lateRate,
              value: '${data.attendance.lateRate}%',
              icon: Icons.warning_amber_rounded,
              tint: AppColors.warning,
            ),
            AppMetricCard(
              title: s.records,
              value: '${data.attendance.totalRecords}',
              icon: Icons.fact_check_outlined,
              tint: const Color(0xFF635BFF),
            ),
          ],
        ),
        const SizedBox(height: 24),
        _StatSection(
          title: s.tasksSection,
          subtitle: s.completionAndQueue,
          cards: [
            AppMetricCard(
              title: s.totalTasks,
              value: '${data.tasks.total}',
              icon: Icons.task_alt_rounded,
              tint: AppColors.accent,
            ),
            AppMetricCard(
              title: s.completionRate,
              value: '${data.tasks.completionRate}%',
              icon: Icons.check_circle_outline_rounded,
              tint: AppColors.success,
            ),
            AppMetricCard(
              title: s.inProgress,
              value: '${data.tasks.inProgress}',
              icon: Icons.timelapse_rounded,
              tint: AppColors.warning,
            ),
            AppMetricCard(
              title: s.pending,
              value: '${data.tasks.pending}',
              icon: Icons.pending_actions_rounded,
              tint: AppColors.warning,
              emphasize: data.tasks.pending > 0,
            ),
          ],
        ),
        const SizedBox(height: 24),
        _StatSection(
          title: s.membersSection,
          subtitle: s.headcountAndRoster,
          cards: [
            AppMetricCard(
              title: s.totalMembers,
              value: '${data.members.total}',
              icon: Icons.groups_rounded,
              tint: AppColors.accent,
            ),
            AppMetricCard(
              title: s.active,
              value: '${data.members.active}',
              icon: Icons.person_pin_circle_outlined,
              tint: AppColors.success,
            ),
            AppMetricCard(
              title: s.leads,
              value: '${data.members.leaderCount}',
              icon: Icons.workspace_premium_outlined,
              tint: const Color(0xFF635BFF),
            ),
            AppMetricCard(
              title: s.admins,
              value: '${data.members.adminCount}',
              icon: Icons.admin_panel_settings_outlined,
              tint: AppColors.warning,
            ),
          ],
        ),
      ],
    );
  }
}

class _StatSection extends StatelessWidget {
  const _StatSection({
    required this.title,
    required this.subtitle,
    required this.cards,
  });

  final String title;
  final String subtitle;
  final List<Widget> cards;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SectionHeader(
          title: title,
          subtitle: subtitle,
        ),
        const SizedBox(height: 16),
        LayoutBuilder(
          builder: (context, constraints) {
            final crossAxisCount = constraints.maxWidth >= 980 ? 4 : 2;
            return GridView.count(
              crossAxisCount: crossAxisCount,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              childAspectRatio: crossAxisCount == 4 ? 1.28 : 1.5,
              children: cards,
            );
          },
        ),
      ],
    );
  }
}

class _InsightSidebar extends StatelessWidget {
  const _InsightSidebar({required this.data});

  final StatisticsOverview data;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SectionHeader(
          title: s.insightLane,
          subtitle: s.insightLaneSubtitle,
        ),
        const SizedBox(height: 16),
        GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(s.reportingPeriod, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 16),
              _InsightRow(label: s.from, value: data.period.from),
              _InsightRow(label: s.to, value: data.period.to),
              _InsightRow(label: s.lateCheckins, value: '${data.attendance.lateCheckins}'),
              _InsightRow(
                label: s.earlyCheckouts,
                value: '${data.attendance.earlyCheckouts}',
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        GlassPanel(
          backgroundColor: const Color(0xE6007AFF),
          borderColor: const Color(0x33007AFF),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                s.desktopNote,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Colors.white,
                    ),
              ),
              const SizedBox(height: 14),
              Text(
                s.desktopNoteText,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.white.withValues(alpha: 0.9),
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _InsightRow extends StatelessWidget {
  const _InsightRow({
    required this.label,
    required this.value,
  });

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
        ],
      ),
    );
  }
}
