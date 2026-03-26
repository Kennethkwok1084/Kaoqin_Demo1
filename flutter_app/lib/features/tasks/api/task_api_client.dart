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
