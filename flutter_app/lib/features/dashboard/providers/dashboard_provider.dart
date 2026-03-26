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
