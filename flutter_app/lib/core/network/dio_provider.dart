// lib/core/network/dio_provider.dart
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../utils/prefs_provider.dart';

final dioProvider = Provider<Dio>((ref) {
  final prefs = ref.watch(prefsProvider);

  // Use environment variable, fallback to localhost for development
  const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000/api/v1',
  );

  final dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      headers: {
        'Content-Type': 'application/json',
      },
    ),
  );

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = prefs.getString('access_token');
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) async {
        final requestOptions = e.requestOptions;
        final refreshToken = prefs.getString('refresh_token');
        final isUnauthorized = e.response?.statusCode == 401;
        final isRefreshRequest = requestOptions.path.endsWith('/auth/refresh');
        final hasRetried = requestOptions.extra['retried'] == true;

        if (!isUnauthorized || isRefreshRequest || hasRetried) {
          return handler.next(e);
        }

        if (refreshToken == null || refreshToken.isEmpty) {
          await prefs.remove('access_token');
          await prefs.remove('refresh_token');
          return handler.next(e);
        }

        try {
          final refreshDio = Dio(
            BaseOptions(
              baseUrl: baseUrl,
              connectTimeout: const Duration(seconds: 15),
              receiveTimeout: const Duration(seconds: 15),
              headers: {
                'Content-Type': 'application/json',
              },
            ),
          );

          final refreshResponse = await refreshDio.post<Map<String, dynamic>>(
            '/auth/refresh',
            data: {
              'refresh_token': refreshToken,
            },
          );

          final responseData =
              refreshResponse.data?['data'] as Map<String, dynamic>?;
          final newAccessToken = responseData?['access_token'] as String?;

          if (newAccessToken == null || newAccessToken.isEmpty) {
            throw StateError('Refresh token response missing access token');
          }

          await prefs.setString('access_token', newAccessToken);

          final retryHeaders =
              Map<String, dynamic>.from(requestOptions.headers);
          retryHeaders['Authorization'] = 'Bearer $newAccessToken';

          final retryOptions = requestOptions.copyWith(
            headers: retryHeaders,
            extra: {
              ...requestOptions.extra,
              'retried': true,
            },
          );

          final response = await dio.fetch<dynamic>(retryOptions);
          return handler.resolve(response);
        } catch (_) {
          await prefs.remove('access_token');
          await prefs.remove('refresh_token');
          return handler.next(e);
        }
      },
    ),
  );

  return dio;
});
