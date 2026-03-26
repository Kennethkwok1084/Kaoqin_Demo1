import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../repositories/auth_repository.dart';

class AuthNotifier extends AsyncNotifier<Map<String, dynamic>?> {
  late AuthRepository _repository;

  @override
  FutureOr<Map<String, dynamic>?> build() async {
    _repository = ref.watch(authRepositoryProvider);
    if (!_repository.isLoggedIn) {
      return null;
    }

    try {
      return await _repository.fetchCurrentUser();
    } catch (_) {
      await _repository.logout();
      return null;
    }
  }

  Future<bool> login(String studentId, String password) async {
    state = const AsyncValue.loading();
    try {
      final loginResponse = await _repository.login(studentId, password);
      final user = loginResponse.user != null
          ? Map<String, dynamic>.from(loginResponse.user!)
          : await _repository.fetchCurrentUser();
      state = AsyncValue.data(user);
      return true;
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      return false;
    }
  }

  Future<void> refreshUser() async {
    state = const AsyncValue.loading();
    try {
      final user = await _repository.fetchCurrentUser();
      state = AsyncValue.data(user);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    state = const AsyncValue.data(null);
  }
}

final authStateProvider = AsyncNotifierProvider<AuthNotifier, Map<String, dynamic>?>(() {
  return AuthNotifier();
});
