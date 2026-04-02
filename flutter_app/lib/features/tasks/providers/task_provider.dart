import 'package:dio/dio.dart';
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
  static const _unset = Object();

  @override
  TaskListParams build() {
    return const TaskListParams();
  }

  void updateParams({
    int? page,
    int? pageSize,
    Object? status = _unset,
    Object? search = _unset,
  }) {
    state = TaskListParams(
      page: page ?? state.page,
      pageSize: pageSize ?? state.pageSize,
      status: identical(status, _unset) ? state.status : status as String?,
      search: identical(search, _unset) ? state.search : search as String?,
    );
  }

  void setPage(int page) {
    state = TaskListParams(
      page: page,
      pageSize: state.pageSize,
      status: state.status,
      search: state.search,
    );
  }

  void setStatus(String? status) {
    state = TaskListParams(
      page: 1,
      pageSize: state.pageSize,
      status: status,
      search: state.search,
    );
  }

  void setSearch(String? search) {
    state = TaskListParams(
      page: 1,
      pageSize: state.pageSize,
      status: state.status,
      search: (search == null || search.trim().isEmpty) ? null : search.trim(),
    );
  }

  void resetFilters() {
    state = TaskListParams(pageSize: state.pageSize);
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

final taskCommandProvider = Provider<TaskCommandService>((ref) {
  final dio = ref.watch(dioProvider);
  return TaskCommandService(dio);
});

final taskDetailProvider =
    FutureProvider.autoDispose.family<TaskDetailItem, int>((ref, taskId) async {
  final service = ref.watch(taskCommandProvider);
  return service.getTaskDetail(taskId);
});

class TaskCommandService {
  TaskCommandService(this._dio);

  final Dio _dio;

  Future<TaskDetailItem> getTaskDetail(int taskId) async {
    final response = await _dio.get<Map<String, dynamic>>('/tasks/repair/$taskId');
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to load task detail',
    );
    return TaskDetailItem.fromJson(data);
  }

  Future<void> startTask(int taskId) async {
    await _postAction('/tasks/$taskId/start');
  }

  Future<void> completeTask(int taskId, {double? actualHours}) async {
    final payload = <String, dynamic>{};
    if (actualHours != null) {
      payload['actualHours'] = actualHours;
    }
    await _postAction('/tasks/$taskId/complete', data: payload);
  }

  Future<void> cancelTask(int taskId, {String? reason}) async {
    final payload = <String, dynamic>{};
    final trimmedReason = reason?.trim();
    if (trimmedReason != null && trimmedReason.isNotEmpty) {
      payload['reason'] = trimmedReason;
    }
    await _postAction('/tasks/$taskId/cancel', data: payload);
  }

  Future<void> _postAction(
    String path, {
    Map<String, dynamic> data = const {},
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(path, data: data);
    if (response.data == null) {
      return;
    }
    if (response.data!['success'] == false) {
      throw Exception(_extractResponseMessage(response.data, 'Request failed'));
    }
  }
}

Map<String, dynamic> _extractResponseData(
  Map<String, dynamic>? response, {
  required String fallbackMessage,
}) {
  if (response == null) {
    throw Exception(fallbackMessage);
  }

  if (response['success'] != true) {
    throw Exception(_extractResponseMessage(response, fallbackMessage));
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

String _extractResponseMessage(
  Map<String, dynamic>? response,
  String fallbackMessage,
) {
  if (response == null) {
    return fallbackMessage;
  }
  return response['message'] as String? ?? fallbackMessage;
}
