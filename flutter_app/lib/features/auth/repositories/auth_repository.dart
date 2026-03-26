import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../core/network/dio_provider.dart';
import '../../../core/utils/prefs_provider.dart';
import '../api/auth_api_client.dart';
import '../models/login_request.dart';
import '../models/login_response.dart';

final authApiClientProvider = Provider<AuthApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return AuthApiClient(dio);
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final apiClient = ref.watch(authApiClientProvider);
  final prefs = ref.watch(prefsProvider);
  return AuthRepository(apiClient, prefs);
});

class AuthRepository {
  final AuthApiClient _apiClient;
  final SharedPreferences _prefs;

  AuthRepository(this._apiClient, this._prefs);

  Future<LoginResponse> login(String studentId, String password) async {
    final response = await _apiClient.login(
      LoginRequest(studentId: studentId, password: password),
    );
    final data = response.data;
    if (data == null) {
      throw Exception('Login data is null');
    }
    await _prefs.setString('access_token', data.accessToken);
    if (data.refreshToken != null) {
      await _prefs.setString('refresh_token', data.refreshToken!);
    }
    return data;
  }

  Future<Map<String, dynamic>> fetchCurrentUser() async {
    final response = await _apiClient.getCurrentUser();
    final data = response.data;
    if (data == null) {
      throw Exception(response.message);
    }
    return Map<String, dynamic>.from(data);
  }

  Future<void> refreshAccessToken() async {
    final refreshToken = this.refreshToken;
    if (refreshToken == null || refreshToken.isEmpty) {
      throw Exception('Refresh token is missing');
    }

    final response = await _apiClient.refresh({
      'refresh_token': refreshToken,
    });
    final data = response.data;
    final accessToken = data?['access_token'] as String?;

    if (accessToken == null || accessToken.isEmpty) {
      throw Exception(response.message);
    }

    await _prefs.setString('access_token', accessToken);
  }

  Future<void> logout() async {
    await _prefs.remove('access_token');
    await _prefs.remove('refresh_token');
  }

  bool get isLoggedIn {
    final token = _prefs.getString('access_token');
    return token != null && token.isNotEmpty;
  }

  String? get accessToken => _prefs.getString('access_token');

  String? get refreshToken => _prefs.getString('refresh_token');
}
