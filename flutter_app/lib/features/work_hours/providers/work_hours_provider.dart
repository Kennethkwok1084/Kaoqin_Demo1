import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/dio_provider.dart';
import '../models/work_hour_models.dart';
import 'dart:async';
import '../api/work_hours_api_client.dart';

final workHoursApiClientProvider = Provider<WorkHoursApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return WorkHoursApiClient(dio);
});

class WorkHoursListNotifier extends Notifier<AsyncValue<List<WorkHourRecord>>> {
  @override
  AsyncValue<List<WorkHourRecord>> build() {
    _fetchRecords();
    return const AsyncValue.loading();
  }

  Future<void> _fetchRecords({int page = 1}) async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(workHoursApiClientProvider);
      // Backend returns a bare List for these records now
      final records = await client.getRecords(page: page);
      state = AsyncValue.data(records);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> refresh() async {
    await _fetchRecords();
  }
}

final workHoursListProvider = NotifierProvider.autoDispose<
    WorkHoursListNotifier, AsyncValue<List<WorkHourRecord>>>(
  () => WorkHoursListNotifier(),
);
