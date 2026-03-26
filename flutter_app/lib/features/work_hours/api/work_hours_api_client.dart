import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';
import '../models/work_hour_models.dart';

part 'work_hours_api_client.g.dart';

@RestApi()
abstract class WorkHoursApiClient {
  factory WorkHoursApiClient(Dio dio, {String baseUrl}) = _WorkHoursApiClient;

  @GET('/attendance/records')
  Future<List<WorkHourRecord>> getRecords({
    @Query('page') int page = 1,
    @Query('size') int size = 20,
    @Query('date_from') String? dateFrom,
    @Query('date_to') String? dateTo,
    @Query('member_id') int? memberId,
  });
}
