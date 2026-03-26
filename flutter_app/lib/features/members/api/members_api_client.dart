import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../../../shared/models/api_response.dart';
import '../../../shared/models/paginated_data.dart';
import '../models/member_models.dart';

part 'members_api_client.g.dart';

@RestApi()
abstract class MembersApiClient {
  factory MembersApiClient(Dio dio, {String? baseUrl}) = _MembersApiClient;

  @GET('/members/')
  Future<ApiResponse<PaginatedData<MemberItem>>> getMembers(
    @Query('page') int page,
    @Query('page_size') int pageSize, {
    @Query('search') String? search,
    @Query('role') String? role,
  });
}
