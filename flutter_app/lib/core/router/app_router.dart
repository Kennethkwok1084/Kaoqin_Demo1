import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'app_shell.dart';
import '../../features/auth/login_screen.dart';
import '../../features/dashboard/dashboard_screen.dart';
import '../../features/tasks/tasks_screen.dart';
import '../../features/work_hours/work_hours_screen.dart';
import '../../features/members/members_screen.dart';
import '../../features/reports/reports_screen.dart';
import '../../features/auth/providers/auth_provider.dart';
import '../../features/auth/repositories/auth_repository.dart';

class _RouterRefreshNotifier extends ChangeNotifier {
  void refresh() {
    notifyListeners();
  }
}

final GlobalKey<NavigatorState> _rootNavigatorKey =
    GlobalKey<NavigatorState>(debugLabel: 'root');
final GlobalKey<NavigatorState> _shellNavigatorDashboardKey =
    GlobalKey<NavigatorState>(debugLabel: 'shellDashboard');
final GlobalKey<NavigatorState> _shellNavigatorTasksKey =
    GlobalKey<NavigatorState>(debugLabel: 'shellTasks');
final GlobalKey<NavigatorState> _shellNavigatorWorkHoursKey =
    GlobalKey<NavigatorState>(debugLabel: 'shellWorkHours');
final GlobalKey<NavigatorState> _shellNavigatorMembersKey =
    GlobalKey<NavigatorState>(debugLabel: 'shellMembers');
final GlobalKey<NavigatorState> _shellNavigatorReportsKey =
    GlobalKey<NavigatorState>(debugLabel: 'shellReports');

final routerProvider = Provider<GoRouter>((ref) {
  final authRepository = ref.read(authRepositoryProvider);
  final refreshNotifier = _RouterRefreshNotifier();

  ref.listen(authStateProvider, (_, __) {
    refreshNotifier.refresh();
  });

  ref.onDispose(refreshNotifier.dispose);

  final router = GoRouter(
    navigatorKey: _rootNavigatorKey,
    refreshListenable: refreshNotifier,
    initialLocation: authRepository.isLoggedIn ? '/dashboard' : '/login',
    redirect: (context, state) {
      final isLoggedIn = authRepository.isLoggedIn;
      final isLoggingIn = state.matchedLocation == '/login';

      if (!isLoggedIn && !isLoggingIn) return '/login';
      if (isLoggedIn && isLoggingIn) return '/dashboard';
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return AppShell(navigationShell: navigationShell);
        },
        branches: [
          StatefulShellBranch(
            navigatorKey: _shellNavigatorDashboardKey,
            routes: [
              GoRoute(
                path: '/dashboard',
                pageBuilder: (context, state) =>
                    const NoTransitionPage(child: DashboardScreen()),
              ),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _shellNavigatorTasksKey,
            routes: [
              GoRoute(
                path: '/tasks',
                pageBuilder: (context, state) =>
                    const NoTransitionPage(child: TasksScreen()),
              ),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _shellNavigatorWorkHoursKey,
            routes: [
              GoRoute(
                path: '/work_hours',
                pageBuilder: (context, state) =>
                    const NoTransitionPage(child: WorkHoursScreen()),
              ),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _shellNavigatorMembersKey,
            routes: [
              GoRoute(
                path: '/members',
                pageBuilder: (context, state) =>
                    const NoTransitionPage(child: MembersScreen()),
              ),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _shellNavigatorReportsKey,
            routes: [
              GoRoute(
                path: '/reports',
                pageBuilder: (context, state) =>
                    const NoTransitionPage(child: ReportsScreen()),
              ),
            ],
          ),
        ],
      ),
    ],
  );

  ref.onDispose(router.dispose);
  return router;
});
