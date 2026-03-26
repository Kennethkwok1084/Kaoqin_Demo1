import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';
import '../../../shared/models/api_response.dart';
import '../models/report_models.dart';

part 'reports_api_client.g.dart';

@RestApi()
abstract class ReportsApiClient {
  factory ReportsApiClient(Dio dio) = _ReportsApiClient;

  @GET('/statistics/overview')
  Future<ApiResponse<StatisticsOverview>> getOverview({
    @Query('date_from') String? dateFrom,
    @Query('date_to') String? dateTo,
  });
}
