import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/dio_provider.dart';
import '../models/report_models.dart';
import 'dart:async';
import '../api/reports_api_client.dart';

final reportsApiClientProvider = Provider<ReportsApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return ReportsApiClient(dio);
});

class StatisticsOverviewNotifier extends Notifier<AsyncValue<StatisticsOverview>> {
  @override
  AsyncValue<StatisticsOverview> build() {
    _fetchOverview();
    return const AsyncValue.loading();
  }

  Future<void> _fetchOverview({String? dateFrom, String? dateTo}) async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(reportsApiClientProvider);
      final response = await client.getOverview(dateFrom: dateFrom, dateTo: dateTo);
      if (!response.success || response.data == null) {
        throw Exception(response.message);
      }
      state = AsyncValue.data(response.data!);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> refresh({String? dateFrom, String? dateTo}) async {
    await _fetchOverview(dateFrom: dateFrom, dateTo: dateTo);
  }
}

final statisticsOverviewProvider = NotifierProvider.autoDispose<StatisticsOverviewNotifier, AsyncValue<StatisticsOverview>>(
  () => StatisticsOverviewNotifier(),
);
