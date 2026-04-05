import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_provider.dart';
import '../models/task_models.dart';

class TaskListParams {
  const TaskListParams({
    this.page = 1,
    this.pageSize = 20,
    this.type = TaskWorkspaceType.repair,
    this.status,
    this.search,
    this.memberId,
  });

  final int page;
  final int pageSize;
  final TaskWorkspaceType type;
  final String? status;
  final String? search;
  final int? memberId;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TaskListParams &&
          runtimeType == other.runtimeType &&
          page == other.page &&
          pageSize == other.pageSize &&
          type == other.type &&
          status == other.status &&
          search == other.search &&
          memberId == other.memberId;

  @override
  int get hashCode => Object.hash(page, pageSize, type, status, search, memberId);
}

class TaskDetailRef {
  const TaskDetailRef({
    required this.taskId,
    required this.type,
  });

  final int taskId;
  final TaskWorkspaceType type;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TaskDetailRef &&
          runtimeType == other.runtimeType &&
          taskId == other.taskId &&
          type == other.type;

  @override
  int get hashCode => Object.hash(taskId, type);
}

class TaskListParamsNotifier extends Notifier<TaskListParams> {
  static const _unset = Object();

  @override
  TaskListParams build() => const TaskListParams();

  void setPage(int page) {
    state = TaskListParams(
      page: page,
      pageSize: state.pageSize,
      type: state.type,
      status: state.status,
      search: state.search,
      memberId: state.memberId,
    );
  }

  void setType(TaskWorkspaceType type) {
    state = TaskListParams(
      page: 1,
      pageSize: state.pageSize,
      type: type,
      status: state.status,
      search: state.search,
      memberId: state.memberId,
    );
  }

  void setStatus(String? status) {
    state = TaskListParams(
      page: 1,
      pageSize: state.pageSize,
      type: state.type,
      status: status,
      search: state.search,
      memberId: state.memberId,
    );
  }

  void setSearch(String? search) {
    final normalized = search?.trim();
    state = TaskListParams(
      page: 1,
      pageSize: state.pageSize,
      type: state.type,
      status: state.status,
      search: (normalized == null || normalized.isEmpty) ? null : normalized,
      memberId: state.memberId,
    );
  }

  void setMemberId(int? memberId) {
    state = TaskListParams(
      page: 1,
      pageSize: state.pageSize,
      type: state.type,
      status: state.status,
      search: state.search,
      memberId: memberId,
    );
  }

  void updateParams({
    int? page,
    int? pageSize,
    Object? type = _unset,
    Object? status = _unset,
    Object? search = _unset,
    Object? memberId = _unset,
  }) {
    final nextSearch = identical(search, _unset) ? state.search : search as String?;
    state = TaskListParams(
      page: page ?? state.page,
      pageSize: pageSize ?? state.pageSize,
      type: identical(type, _unset) ? state.type : type as TaskWorkspaceType,
      status: identical(status, _unset) ? state.status : status as String?,
      search: nextSearch == null || nextSearch.trim().isEmpty ? null : nextSearch.trim(),
      memberId: identical(memberId, _unset) ? state.memberId : memberId as int?,
    );
  }

  void resetFilters() {
    state = TaskListParams(
      pageSize: state.pageSize,
      type: state.type,
    );
  }
}

final taskListParamsProvider =
    NotifierProvider<TaskListParamsNotifier, TaskListParams>(
  TaskListParamsNotifier.new,
);

final taskCommandProvider = Provider<TaskCommandService>((ref) {
  final dio = ref.watch(dioProvider);
  return TaskCommandService(dio);
});

final taskListProvider = FutureProvider<PaginatedData<TaskItem>>((ref) async {
  final params = ref.watch(taskListParamsProvider);
  final service = ref.watch(taskCommandProvider);
  return service.getTasks(params);
});

final taskStatsProvider = FutureProvider<TaskStats>((ref) async {
  final params = ref.watch(taskListParamsProvider);
  final service = ref.watch(taskCommandProvider);
  return service.getTaskStats(params.type);
});

final taskAssigneeOptionsProvider = FutureProvider<List<TaskAssigneeOption>>((ref) async {
  final service = ref.watch(taskCommandProvider);
  return service.getRepairAssignees();
});

final taskDetailProvider =
    FutureProvider.autoDispose.family<TaskDetailItem, TaskDetailRef>((ref, detailRef) async {
  final service = ref.watch(taskCommandProvider);
  return service.getTaskDetail(detailRef);
});

class TaskCommandService {
  TaskCommandService(this._dio);

  final Dio _dio;

  Future<PaginatedData<TaskItem>> getTasks(TaskListParams params) async {
    final response = await _dio.get<Map<String, dynamic>>(
      _listPath(params.type),
      queryParameters: _listQuery(params),
    );
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to load tasks',
    );
    return PaginatedData<TaskItem>.fromJson(
      data,
      (json) => TaskItem.fromJson(json, fallbackType: params.type),
    );
  }

  Future<TaskStats> getTaskStats(TaskWorkspaceType type) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/tasks/stats',
      queryParameters: {'task_type': type.apiValue},
    );
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to load task statistics',
    );
    return TaskStats.fromJson(data);
  }

  Future<TaskDetailItem> getTaskDetail(TaskDetailRef detailRef) async {
    final response = await _dio.get<Map<String, dynamic>>(
      _detailPath(detailRef),
    );
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to load task detail',
    );
    return TaskDetailItem.fromJson(data);
  }

  Future<List<TaskAssigneeOption>> getRepairAssignees() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/members/',
      queryParameters: const <String, dynamic>{
        'page': 1,
        'page_size': 100,
        'is_active': true,
      },
    );
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to load repair assignees',
    );
    final items = data['items'] as List<dynamic>? ?? const [];
    return items
        .whereType<Map>()
        .map((item) => TaskAssigneeOption.fromJson(Map<String, dynamic>.from(item)))
        .toList(growable: false);
  }

  Future<void> startTask(int taskId) async {
    await _postAction('/tasks/$taskId/start');
  }

  Future<Map<String, dynamic>> createRepairTask(Map<String, dynamic> payload) async {
    return _requestData(
      () => _dio.post<Map<String, dynamic>>('/tasks/repair', data: payload),
      fallbackMessage: 'Failed to create repair task',
    );
  }

  Future<Map<String, dynamic>> updateRepairTask(
    int taskId,
    Map<String, dynamic> payload,
  ) async {
    return _requestData(
      () => _dio.put<Map<String, dynamic>>('/tasks/repair/$taskId', data: payload),
      fallbackMessage: 'Failed to update repair task',
    );
  }

  Future<void> deleteRepairTask(int taskId) async {
    await _requestMessage(
      () => _dio.delete<Map<String, dynamic>>('/tasks/repair/$taskId'),
      fallbackMessage: 'Failed to delete repair task',
    );
  }

  Future<Map<String, dynamic>> batchDeleteRepairTasks(List<int> taskIds) async {
    return _requestData(
      () => _dio.post<Map<String, dynamic>>(
        '/tasks/batch-delete',
        data: {'task_ids': taskIds},
      ),
      fallbackMessage: 'Failed to batch delete repair tasks',
    );
  }

  Future<RepairImportTemplate> getRepairImportTemplate() async {
    final data = await _requestData(
      () => _dio.get<Map<String, dynamic>>('/tasks/maintenance-orders/template'),
      fallbackMessage: 'Failed to load import template',
    );
    return RepairImportTemplate.fromJson(data);
  }

  Future<RepairImportPreview> previewRepairImport(
    XFile file, {
    bool skipDuplicates = true,
  }) async {
    final bytes = await file.readAsBytes();
    final data = await _requestData(
      () => _dio.post<Map<String, dynamic>>(
        '/tasks/maintenance-orders/import-excel',
        data: FormData.fromMap({
          'file': MultipartFile.fromBytes(
            bytes,
            filename: file.name,
          ),
          'dry_run': true,
          'skip_duplicates': skipDuplicates,
        }),
      ),
      fallbackMessage: 'Failed to preview import file',
    );
    return RepairImportPreview.fromJson(data);
  }

  Future<RepairImportResult> importRepairExcel(
    XFile file, {
    bool skipDuplicates = true,
  }) async {
    final bytes = await file.readAsBytes();
    final data = await _requestData(
      () => _dio.post<Map<String, dynamic>>(
        '/tasks/maintenance-orders/import-excel',
        data: FormData.fromMap({
          'file': MultipartFile.fromBytes(
            bytes,
            filename: file.name,
          ),
          'dry_run': false,
          'skip_duplicates': skipDuplicates,
        }),
      ),
      fallbackMessage: 'Failed to import maintenance orders',
    );
    return RepairImportResult.fromJson(data);
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

  Map<String, dynamic> _listQuery(TaskListParams params) {
    switch (params.type) {
      case TaskWorkspaceType.repair:
        return <String, dynamic>{
          'page': params.page,
          'pageSize': params.pageSize,
          if (params.status != null) 'status': params.status,
          if (params.search != null) 'search': params.search,
          if (params.memberId != null) 'member_id': params.memberId,
        };
      case TaskWorkspaceType.monitoring:
      case TaskWorkspaceType.assistance:
        return <String, dynamic>{
          'page': params.page,
          'pageSize': params.pageSize,
        };
    }
  }

  String _listPath(TaskWorkspaceType type) => switch (type) {
        TaskWorkspaceType.repair => '/tasks/repair',
        TaskWorkspaceType.monitoring => '/tasks/monitoring/list',
        TaskWorkspaceType.assistance => '/tasks/assistance/list',
      };

  String _detailPath(TaskDetailRef detailRef) => switch (detailRef.type) {
        TaskWorkspaceType.repair => '/tasks/repair/${detailRef.taskId}',
        TaskWorkspaceType.monitoring => '/tasks/monitoring/${detailRef.taskId}/inspection',
        TaskWorkspaceType.assistance => '/tasks/assistance/${detailRef.taskId}',
      };

  Future<Map<String, dynamic>> _requestData(
    Future<Response<Map<String, dynamic>>> Function() request, {
    required String fallbackMessage,
  }) async {
    final response = await request();
    return _extractResponseData(response.data, fallbackMessage: fallbackMessage);
  }

  Future<String> _requestMessage(
    Future<Response<Map<String, dynamic>>> Function() request, {
    required String fallbackMessage,
  }) async {
    final response = await request();
    if (response.data == null) {
      throw Exception(fallbackMessage);
    }
    if (response.data!['success'] != true) {
      throw Exception(_extractResponseMessage(response.data, fallbackMessage));
    }
    return _extractResponseMessage(response.data, fallbackMessage);
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
