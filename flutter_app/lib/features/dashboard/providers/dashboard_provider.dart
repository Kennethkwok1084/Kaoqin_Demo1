import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_provider.dart';
import '../api/dashboard_api_client.dart';
import '../models/dashboard_models.dart';

final dashboardApiClientProvider = Provider<DashboardApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return DashboardApiClient(dio);
});

final dashboardOverviewProvider = FutureProvider<DashboardOverviewResponse>((ref) async {
  final client = ref.watch(dashboardApiClientProvider);
  final response = await client.getOverview();
  
  if (response.success && response.data != null) {
    return response.data!;
  } else {
    throw Exception(response.message);
  }
});

final dashboardScreenProvider = FutureProvider<DashboardScreenData>((ref) async {
  final client = ref.watch(dashboardApiClientProvider);
  final dio = ref.watch(dioProvider);

  final overviewResponse = await client.getOverview();
  if (!overviewResponse.success || overviewResponse.data == null) {
    throw Exception(overviewResponse.message);
  }

  final myTasksRaw = await dio.get<Map<String, dynamic>>(
    '/dashboard/my-tasks',
    queryParameters: const {'limit': 5},
  );
  final myTasksPayload = _extractResponseData(
    myTasksRaw.data,
    fallbackMessage: 'Failed to load dashboard tasks',
  );

  final myTasks = ((myTasksPayload['tasks'] as List<dynamic>?) ?? const [])
      .where((item) => item is Map)
      .map((item) => DashboardTaskSummaryItem.fromJson(Map<String, dynamic>.from(item as Map)))
      .toList();
  final taskStats = DashboardTaskStatsData.fromJson(
    Map<String, dynamic>.from(
      (myTasksPayload['summary'] as Map<String, dynamic>?) ?? const {},
    ),
  );

  final memberPerformanceRaw = await dio.get<List<dynamic>>(
    '/dashboard/member-performance',
    queryParameters: const {'limit': 5},
  );
  final memberPerformance = (memberPerformanceRaw.data ?? const [])
      .where((item) => item is Map)
      .map((item) => DashboardMemberPerformanceItem.fromJson(Map<String, dynamic>.from(item as Map)))
      .toList();

  final alertsRaw = await dio.get<List<dynamic>>(
    '/dashboard/alerts',
    queryParameters: const {'resolved': false},
  );
  final alerts = (alertsRaw.data ?? const [])
      .where((item) => item is Map)
      .map((item) => DashboardAlertItem.fromJson(Map<String, dynamic>.from(item as Map)))
      .toList();

  return DashboardScreenData(
    overview: overviewResponse.data!,
    myTasks: myTasks,
    taskStats: taskStats,
    memberPerformance: memberPerformance,
    alerts: alerts,
  );
});

Map<String, dynamic> _extractResponseData(
  Map<String, dynamic>? response, {
  required String fallbackMessage,
}) {
  if (response == null) {
    throw Exception(fallbackMessage);
  }

  final success = response['success'] == true;
  if (!success) {
    throw Exception(response['message'] as String? ?? fallbackMessage);
  }

  final data = response['data'];
  if (data is Map<String, dynamic>) {
    return data;
  }
  if (data is Map) {
    return Map<String, dynamic>.from(data);
  }

  throw Exception(fallbackMessage);
}
