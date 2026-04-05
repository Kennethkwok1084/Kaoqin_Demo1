import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/providers/auth_provider.dart';
import '../localization/app_locale.dart';
import '../localization/app_strings.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/glass_panel.dart';

class AppShell extends ConsumerWidget {
  const AppShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  void _goToBranch(int index) {
    navigationShell.goBranch(
      index,
      initialLocation: index == navigationShell.currentIndex,
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.strings;
    final language = ref.watch(appLanguageProvider);
    final authState = ref.watch(authStateProvider);
    final user = authState.asData?.value;
    final displayName = _resolveDisplayName(user);
    final avatarText = displayName.substring(0, 1).toUpperCase();
    final destinations = [
      _ShellDestination(
        label: s.dashboardNav,
        subtitle: s.overview,
        icon: Icons.dashboard_outlined,
        selectedIcon: Icons.dashboard_rounded,
      ),
      _ShellDestination(
        label: s.tasksNav,
        subtitle: s.taskQueue,
        icon: Icons.task_alt_outlined,
        selectedIcon: Icons.task_alt_rounded,
        badge: '5',
      ),
      _ShellDestination(
        label: s.workHoursNav,
        subtitle: s.hoursAndAttendance,
        icon: Icons.schedule_outlined,
        selectedIcon: Icons.schedule_rounded,
      ),
      _ShellDestination(
        label: s.membersNav,
        subtitle: s.peopleAndSchedule,
        icon: Icons.people_outline_rounded,
        selectedIcon: Icons.people_rounded,
      ),
      _ShellDestination(
        label: s.reportsNav,
        subtitle: s.analytics,
        icon: Icons.analytics_outlined,
        selectedIcon: Icons.analytics_rounded,
      ),
    ];
    final current = destinations[navigationShell.currentIndex];

    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 1180;

        return Scaffold(
          body: DecoratedBox(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color(0xFFF7F9FF),
                  Color(0xFFF2F2F7),
                  Color(0xFFEAF0FF),
                ],
              ),
            ),
            child: SafeArea(
              minimum: EdgeInsets.all(compact ? 12 : 16),
              child: compact
                  ? _CompactShell(
                      current: current,
                      displayName: displayName,
                      avatarText: avatarText,
                      language: language,
                      currentIndex: navigationShell.currentIndex,
                      destinations: destinations,
                      onDestinationSelected: _goToBranch,
                      onToggleLanguage: () =>
                          ref.read(appLanguageProvider.notifier).toggle(),
                      onLogout: () async {
                        await ref.read(authStateProvider.notifier).logout();
                      },
                      child: navigationShell,
                    )
                  : _WideShell(
                      current: current,
                      displayName: displayName,
                      avatarText: avatarText,
                      language: language,
                      currentIndex: navigationShell.currentIndex,
                      destinations: destinations,
                      onDestinationSelected: _goToBranch,
                      onToggleLanguage: () =>
                          ref.read(appLanguageProvider.notifier).toggle(),
                      onLogout: () async {
                        await ref.read(authStateProvider.notifier).logout();
                      },
                      child: navigationShell,
                    ),
            ),
          ),
        );
      },
    );
  }

  String _resolveDisplayName(Map<String, dynamic>? user) {
    final rawName = (user?['name'] as String?)?.trim();
    final rawUsername = (user?['username'] as String?)?.trim();

    if (rawName != null && rawName.isNotEmpty) {
      return rawName;
    }
    if (rawUsername != null && rawUsername.isNotEmpty) {
      return rawUsername;
    }
    return 'Operator';
  }
}

class _WideShell extends StatelessWidget {
  const _WideShell({
    required this.current,
    required this.displayName,
    required this.avatarText,
    required this.language,
    required this.currentIndex,
    required this.destinations,
    required this.onDestinationSelected,
    required this.onToggleLanguage,
    required this.onLogout,
    required this.child,
  });

  final _ShellDestination current;
  final String displayName;
  final String avatarText;
  final AppLanguage language;
  final int currentIndex;
  final List<_ShellDestination> destinations;
  final ValueChanged<int> onDestinationSelected;
  final Future<void> Function() onToggleLanguage;
  final Future<void> Function() onLogout;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;

    return Row(
      children: [
        SizedBox(
          width: 268,
          child: GlassPanel(
            padding: const EdgeInsets.fromLTRB(18, 20, 18, 16),
            radius: 30,
            backgroundColor: Colors.white.withValues(alpha: 0.62),
            borderColor: AppColors.borderStrong.withValues(alpha: 0.8),
            blur: 22,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _BrandBlock(),
                const SizedBox(height: 28),
                Expanded(
                  child: ListView.separated(
                    padding: EdgeInsets.zero,
                    itemCount: destinations.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, index) => _SidebarItem(
                      destination: destinations[index],
                      selected: index == currentIndex,
                      onTap: () => onDestinationSelected(index),
                    ),
                  ),
                ),
                Divider(color: AppColors.borderStrong.withValues(alpha: 0.9)),
                const SizedBox(height: 10),
                _SidebarAction(
                  icon: Icons.language_rounded,
                  label: language == AppLanguage.zh
                      ? s.languageEnglish
                      : s.languageChinese,
                  onTap: onToggleLanguage,
                ),
                const SizedBox(height: 6),
                _SidebarAction(
                  icon: Icons.settings_outlined,
                  label: s.settings,
                  onTap: () {},
                ),
                const SizedBox(height: 6),
                _SidebarAction(
                  icon: Icons.logout_rounded,
                  label: s.signOut,
                  foregroundColor: AppColors.danger,
                  onTap: onLogout,
                ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            children: [
              _TopToolbar(
                current: current,
                displayName: displayName,
                avatarText: avatarText,
                language: language,
                onToggleLanguage: onToggleLanguage,
              ),
              const SizedBox(height: 16),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(32),
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.34),
                      border: Border.all(color: AppColors.borderStrong),
                    ),
                    child: child,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _CompactShell extends StatelessWidget {
  const _CompactShell({
    required this.current,
    required this.displayName,
    required this.avatarText,
    required this.language,
    required this.currentIndex,
    required this.destinations,
    required this.onDestinationSelected,
    required this.onToggleLanguage,
    required this.onLogout,
    required this.child,
  });

  final _ShellDestination current;
  final String displayName;
  final String avatarText;
  final AppLanguage language;
  final int currentIndex;
  final List<_ShellDestination> destinations;
  final ValueChanged<int> onDestinationSelected;
  final Future<void> Function() onToggleLanguage;
  final Future<void> Function() onLogout;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _TopToolbar(
          current: current,
          displayName: displayName,
          avatarText: avatarText,
          language: language,
          onToggleLanguage: onToggleLanguage,
          compact: true,
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(28),
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.48),
                border: Border.all(color: AppColors.borderStrong),
              ),
              child: child,
            ),
          ),
        ),
        const SizedBox(height: 12),
        GlassPanel(
          radius: 24,
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
          child: Row(
            children: [
              for (var index = 0; index < destinations.length; index++)
                Expanded(
                  child: _CompactNavButton(
                    destination: destinations[index],
                    selected: index == currentIndex,
                    onTap: () => onDestinationSelected(index),
                  ),
                ),
              IconButton(
                onPressed: onToggleLanguage,
                icon: Text(
                  language == AppLanguage.zh ? 'EN' : '中',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w500,
                      ),
                ),
                style: IconButton.styleFrom(
                  backgroundColor: AppColors.surfaceStrong,
                  foregroundColor: AppColors.textPrimary,
                ),
              ),
              const SizedBox(width: 6),
              IconButton(
                onPressed: onLogout,
                icon: const Icon(Icons.logout_rounded),
                style: IconButton.styleFrom(
                  backgroundColor: AppColors.surfaceStrong,
                  foregroundColor: AppColors.danger,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _TopToolbar extends StatelessWidget {
  const _TopToolbar({
    required this.current,
    required this.displayName,
    required this.avatarText,
    required this.language,
    required this.onToggleLanguage,
    this.compact = false,
  });

  final _ShellDestination current;
  final String displayName;
  final String avatarText;
  final AppLanguage language;
  final Future<void> Function() onToggleLanguage;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final searchField = SizedBox(
      width: compact ? double.infinity : 300,
      child: TextField(
        decoration: InputDecoration(
          hintText: s.searchHint,
          prefixIcon: const Icon(
            Icons.search_rounded,
            color: AppColors.textSecondary,
          ),
          suffixIcon: Container(
            margin: const EdgeInsets.all(8),
            width: 28,
            decoration: BoxDecoration(
              color: AppColors.background,
              borderRadius: BorderRadius.circular(999),
            ),
            child: const Icon(
              Icons.keyboard_command_key_rounded,
              size: 16,
              color: AppColors.textSecondary,
            ),
          ),
        ),
      ),
    );

    final userChip = Container(
      padding: const EdgeInsets.fromLTRB(8, 8, 14, 8),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.72),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.borderStrong),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [
                  AppColors.accent,
                  Color(0xFF5B64F6),
                ],
              ),
              borderRadius: BorderRadius.circular(999),
            ),
            alignment: Alignment.center,
            child: Text(
              avatarText,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                displayName,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontFamily: AppTypography.fontFamily,
                      fontFamilyFallback: AppTypography.fontFamilyFallback,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textPrimary,
                    ),
              ),
              Text(
                current.subtitle,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ],
      ),
    );

    return GlassPanel(
      radius: 28,
      padding: EdgeInsets.fromLTRB(compact ? 18 : 28, 18, 20, 18),
      backgroundColor: Colors.white.withValues(alpha: 0.58),
      borderColor: AppColors.borderStrong.withValues(alpha: 0.8),
      blur: 18,
      child: compact
          ? Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  s.departmentName,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontFamily: AppTypography.fontFamily,
                        fontFamilyFallback: AppTypography.fontFamilyFallback,
                        color: AppColors.accent,
                        fontWeight: FontWeight.w500,
                        letterSpacing: 0.3,
                      ),
                ),
                const SizedBox(height: 6),
                Text(
                  current.label,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontSize: 28,
                      ),
                ),
                const SizedBox(height: 14),
                searchField,
                const SizedBox(height: 12),
                Row(
                  children: [
                    const _NotificationButton(),
                    const SizedBox(width: 10),
                    IconButton(
                      onPressed: onToggleLanguage,
                      icon: Text(
                        language == AppLanguage.zh ? 'EN' : '中',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontFamily: AppTypography.fontFamily,
                              fontFamilyFallback: AppTypography.fontFamilyFallback,
                              color: AppColors.textPrimary,
                              fontWeight: FontWeight.w500,
                            ),
                      ),
                      style: IconButton.styleFrom(
                        backgroundColor: Colors.white.withValues(alpha: 0.72),
                        foregroundColor: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(child: userChip),
                  ],
                ),
              ],
            )
          : Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        s.departmentName,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontFamily: AppTypography.fontFamily,
                              fontFamilyFallback: AppTypography.fontFamilyFallback,
                              color: AppColors.accent,
                              fontWeight: FontWeight.w500,
                              letterSpacing: 0.3,
                            ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        current.label,
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                              fontSize: 28,
                            ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                searchField,
                const SizedBox(width: 12),
                IconButton(
                  onPressed: onToggleLanguage,
                  icon: Text(
                    language == AppLanguage.zh ? 'EN' : '中',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          fontFamily: AppTypography.fontFamily,
                          fontFamilyFallback: AppTypography.fontFamilyFallback,
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w500,
                        ),
                  ),
                  style: IconButton.styleFrom(
                    backgroundColor: Colors.white.withValues(alpha: 0.72),
                    foregroundColor: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(width: 12),
                const _NotificationButton(),
                const SizedBox(width: 12),
                userChip,
              ],
            ),
    );
  }
}

class _BrandBlock extends StatelessWidget {
  const _BrandBlock();

  @override
  Widget build(BuildContext context) {
    final s = context.strings;

    return Row(
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: AppColors.accent,
            borderRadius: BorderRadius.circular(16),
            boxShadow: const [
              BoxShadow(
                color: Color(0x33007AFF),
                blurRadius: 18,
                offset: Offset(0, 10),
              ),
            ],
          ),
          child: const Icon(
            Icons.access_time_rounded,
            color: Colors.white,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                s.appTitle,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontFamily: AppTypography.fontFamily,
                      fontFamilyFallback: AppTypography.fontFamilyFallback,
                      fontWeight: FontWeight.w600,
                    ),
              ),
              const SizedBox(height: 4),
              Text(
                s.departmentName,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _SidebarItem extends StatelessWidget {
  const _SidebarItem({
    required this.destination,
    required this.selected,
    required this.onTap,
  });

  final _ShellDestination destination;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final icon = selected ? destination.selectedIcon : destination.icon;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          curve: Curves.easeOut,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            color: selected ? AppColors.accent : Colors.transparent,
            boxShadow: selected
                ? const [
                    BoxShadow(
                      color: Color(0x29007AFF),
                      blurRadius: 18,
                      offset: Offset(0, 10),
                    ),
                  ]
                : null,
          ),
          child: Row(
            children: [
              Icon(
                icon,
                color: selected ? Colors.white : AppColors.textSecondary,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  destination.label,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontFamily: AppTypography.fontFamily,
                        fontFamilyFallback: AppTypography.fontFamilyFallback,
                        color: selected ? Colors.white : AppColors.textPrimary,
                        fontWeight: FontWeight.w500,
                      ),
                ),
              ),
              if (destination.badge != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: selected
                        ? Colors.white.withValues(alpha: 0.16)
                        : const Color(0x22FF453A),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    destination.badge!,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          fontFamily: AppTypography.fontFamily,
                          fontFamilyFallback: AppTypography.fontFamilyFallback,
                          color: selected ? Colors.white : AppColors.danger,
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CompactNavButton extends StatelessWidget {
  const _CompactNavButton({
    required this.destination,
    required this.selected,
    required this.onTap,
  });

  final _ShellDestination destination;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              selected ? destination.selectedIcon : destination.icon,
              color: selected ? AppColors.accent : AppColors.textSecondary,
            ),
            const SizedBox(height: 4),
            Text(
              destination.label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontFamily: AppTypography.fontFamily,
                    fontFamilyFallback: AppTypography.fontFamilyFallback,
                    color: selected ? AppColors.accent : AppColors.textSecondary,
                    fontWeight: FontWeight.w500,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SidebarAction extends StatelessWidget {
  const _SidebarAction({
    required this.icon,
    required this.label,
    required this.onTap,
    this.foregroundColor = AppColors.textSecondary,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final Color foregroundColor;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
        child: Row(
          children: [
            Icon(icon, color: foregroundColor, size: 20),
            const SizedBox(width: 10),
            Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontFamily: AppTypography.fontFamily,
                    fontFamilyFallback: AppTypography.fontFamilyFallback,
                    color: foregroundColor,
                    fontWeight: FontWeight.w500,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NotificationButton extends StatelessWidget {
  const _NotificationButton();

  @override
  Widget build(BuildContext context) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(999),
            onTap: () {},
            child: Ink(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.72),
                borderRadius: BorderRadius.circular(999),
                border: Border.all(color: AppColors.borderStrong),
              ),
              child: const Icon(
                Icons.notifications_none_rounded,
                color: AppColors.textPrimary,
              ),
            ),
          ),
        ),
        Positioned(
          right: 2,
          top: 2,
          child: Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: AppColors.danger,
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: AppColors.background, width: 2),
            ),
          ),
        ),
      ],
    );
  }
}

class _ShellDestination {
  const _ShellDestination({
    required this.label,
    required this.subtitle,
    required this.icon,
    required this.selectedIcon,
    this.badge,
  });

  final String label;
  final String subtitle;
  final IconData icon;
  final IconData selectedIcon;
  final String? badge;
}
