import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_provider.dart';
import '../api/task_api_client.dart';
import '../models/task_models.dart';

final taskApiClientProvider = Provider<TaskApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return TaskApiClient(dio);
});

// A provider for pagination state to easily refresh or change page
class TaskListParams {
  final int page;
  final int pageSize;
  final String? status;
  final String? search;

  const TaskListParams({
    this.page = 1,
    this.pageSize = 20,
    this.status,
    this.search,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TaskListParams &&
          runtimeType == other.runtimeType &&
          page == other.page &&
          pageSize == other.pageSize &&
          status == other.status &&
          search == other.search;

  @override
  int get hashCode => page.hashCode ^ pageSize.hashCode ^ status.hashCode ^ search.hashCode;
}

class TaskListParamsNotifier extends Notifier<TaskListParams> {
  @override
  TaskListParams build() {
    return const TaskListParams();
  }

  void updateParams({int? page, int? pageSize, String? status, String? search}) {
    state = TaskListParams(
      page: page ?? state.page,
      pageSize: pageSize ?? state.pageSize,
      status: status ?? state.status,
      search: search ?? state.search,
    );
  }
}

final taskListParamsProvider = NotifierProvider<TaskListParamsNotifier, TaskListParams>(() {
  return TaskListParamsNotifier();
});

final taskListProvider = FutureProvider<PaginatedData<TaskItem>>((ref) async {
  final client = ref.watch(taskApiClientProvider);
  final params = ref.watch(taskListParamsProvider);
  
  final response = await client.getTasks(
    params.page,
    params.pageSize,
    status: params.status,
    search: params.search,
  );

  if (response.success && response.data != null) {
    return response.data!;
  } else {
    throw Exception(response.message);
  }
});
