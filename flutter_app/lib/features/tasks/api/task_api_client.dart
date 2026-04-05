import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../../../shared/models/api_response.dart';
import '../models/task_models.dart';

part 'task_api_client.g.dart';

@RestApi()
abstract class TaskApiClient {
  factory TaskApiClient(Dio dio, {String? baseUrl}) = _TaskApiClient;

  @GET('/tasks/repair')
  Future<ApiResponse<PaginatedData<TaskItem>>> getTasks(
    @Query('page') int page,
    @Query('pageSize') int pageSize, {
    @Query('status') String? status,
    @Query('search') String? search,
  });
}

class TaskApiPaths {
  const TaskApiPaths._();

  static String list(TaskWorkspaceType section) {
    switch (section) {
      case TaskWorkspaceType.repair:
        return '/tasks/repair';
      case TaskWorkspaceType.monitoring:
        return '/tasks/monitoring/list';
      case TaskWorkspaceType.assistance:
        return '/tasks/assistance/list';
    }
  }

  static String detail(TaskWorkspaceType section, int taskId) {
    switch (section) {
      case TaskWorkspaceType.repair:
        return '/tasks/repair/$taskId';
      case TaskWorkspaceType.monitoring:
        return '/tasks/monitoring/$taskId/inspection';
      case TaskWorkspaceType.assistance:
        return '/tasks/assistance/$taskId';
    }
  }

  static String startRepair(int taskId) => '/tasks/$taskId/start';
  static String completeRepair(int taskId) => '/tasks/$taskId/complete';
  static String cancelRepair(int taskId) => '/tasks/$taskId/cancel';

  static String updateMonitoringInspection(int taskId) =>
      '/tasks/monitoring/$taskId/inspection';

  static String completeMonitoringInspection(int taskId) =>
      '/tasks/monitoring/$taskId/inspection/complete';

  static String reviewAssistance(int taskId) => '/tasks/assistance/$taskId/review';
  static String batchReviewAssistance() => '/tasks/assistance/batch-review';
}
