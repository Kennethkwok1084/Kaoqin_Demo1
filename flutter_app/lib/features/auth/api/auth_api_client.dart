import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';
import '../models/login_request.dart';
import '../models/login_response.dart';
import '../../../shared/models/api_response.dart';

part 'auth_api_client.g.dart';

@RestApi()
abstract class AuthApiClient {
  factory AuthApiClient(Dio dio, {String? baseUrl}) = _AuthApiClient;

  @POST('/auth/login')
  Future<ApiResponse<LoginResponse>> login(@Body() LoginRequest request);

  @POST('/auth/refresh')
  Future<ApiResponse<Map<String, dynamic>>> refresh(
    @Body() Map<String, dynamic> request,
  );

  @GET('/auth/me')
  Future<ApiResponse<Map<String, dynamic>>> getCurrentUser();
}
