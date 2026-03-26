import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../../../shared/models/api_response.dart';
import '../models/dashboard_models.dart';

part 'dashboard_api_client.g.dart';

@RestApi()
abstract class DashboardApiClient {
  factory DashboardApiClient(Dio dio, {String? baseUrl}) = _DashboardApiClient;

  @GET('/dashboard/overview')
  Future<ApiResponse<DashboardOverviewResponse>> getOverview();
}
