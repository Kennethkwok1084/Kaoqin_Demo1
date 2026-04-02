import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_provider.dart';
import '../../../shared/models/paginated_data.dart';
import '../models/member_models.dart';

final membersCommandProvider = Provider<MembersCommandService>((ref) {
  final dio = ref.watch(dioProvider);
  return MembersCommandService(dio);
});

class MembersParams {
  final int page;
  final int pageSize;
  final String? search;
  final String? role;
  final bool? isActive;
  final String? department;
  final String? className;

  const MembersParams({
    this.page = 1,
    this.pageSize = 20,
    this.search,
    this.role,
    this.isActive,
    this.department,
    this.className,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is MembersParams &&
          runtimeType == other.runtimeType &&
          page == other.page &&
          pageSize == other.pageSize &&
          search == other.search &&
          role == other.role &&
          isActive == other.isActive &&
          department == other.department &&
          className == other.className;

  @override
  int get hashCode =>
      Object.hash(page, pageSize, search, role, isActive, department, className);
}

class MembersParamsNotifier extends Notifier<MembersParams> {
  static const _unset = Object();

  @override
  MembersParams build() => const MembersParams();

  void updateParams({
    int? page,
    int? pageSize,
    Object? search = _unset,
    Object? role = _unset,
    Object? isActive = _unset,
    Object? department = _unset,
    Object? className = _unset,
  }) {
    state = MembersParams(
      page: page ?? state.page,
      pageSize: pageSize ?? state.pageSize,
      search: identical(search, _unset) ? state.search : _normalizeText(search as String?),
      role: identical(role, _unset) ? state.role : _normalizeText(role as String?),
      isActive: identical(isActive, _unset) ? state.isActive : isActive as bool?,
      department: identical(department, _unset)
          ? state.department
          : _normalizeText(department as String?),
      className: identical(className, _unset)
          ? state.className
          : _normalizeText(className as String?),
    );
  }

  void setPage(int page) {
    state = MembersParams(
      page: page,
      pageSize: state.pageSize,
      search: state.search,
      role: state.role,
      isActive: state.isActive,
      department: state.department,
      className: state.className,
    );
  }

  void applyFilters({
    String? search,
    String? role,
    bool? isActive,
    String? department,
    String? className,
  }) {
    state = MembersParams(
      page: 1,
      pageSize: state.pageSize,
      search: _normalizeText(search),
      role: _normalizeText(role),
      isActive: isActive,
      department: _normalizeText(department),
      className: _normalizeText(className),
    );
  }

  void resetFilters() {
    state = MembersParams(pageSize: state.pageSize);
  }
}

final membersParamsProvider = NotifierProvider<MembersParamsNotifier, MembersParams>(() {
  return MembersParamsNotifier();
});

final membersListProvider = FutureProvider<PaginatedData<MemberItem>>((ref) async {
  final service = ref.watch(membersCommandProvider);
  final params = ref.watch(membersParamsProvider);
  return service.getMembers(params);
});

final memberStatsProvider = FutureProvider<MemberStats>((ref) async {
  final service = ref.watch(membersCommandProvider);
  return service.getStats();
});

class MemberStats {
  const MemberStats({
    required this.totalMembers,
    required this.activeMembers,
    required this.inactiveMembers,
    required this.roleStats,
    required this.departmentStats,
  });

  final int totalMembers;
  final int activeMembers;
  final int inactiveMembers;
  final Map<String, int> roleStats;
  final Map<String, int> departmentStats;

  factory MemberStats.fromJson(Map<String, dynamic> json) {
    return MemberStats(
      totalMembers: _readInt(json['total_members']),
      activeMembers: _readInt(json['active_members']),
      inactiveMembers: _readInt(json['inactive_members']),
      roleStats: _readIntMap(json['role_stats']),
      departmentStats: _readIntMap(json['department_stats']),
    );
  }
}

class MembersCommandService {
  MembersCommandService(this._dio);

  final Dio _dio;

  Future<PaginatedData<MemberItem>> getMembers(MembersParams params) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/members/',
      queryParameters: <String, dynamic>{
        'page': params.page,
        'page_size': params.pageSize,
        if (params.search != null) 'search': params.search,
        if (params.role != null) 'role': params.role,
        if (params.isActive != null) 'is_active': params.isActive,
        if (params.department != null) 'department': params.department,
        if (params.className != null) 'class_name': params.className,
      },
    );

    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to load members',
    );

    return PaginatedData<MemberItem>.fromJson(
      data,
      (json) => MemberItem.fromJson(Map<String, dynamic>.from(json as Map)),
    );
  }

  Future<MemberStats> getStats() async {
    final response = await _dio.get<Map<String, dynamic>>('/members/stats/overview');
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to load member statistics',
    );
    return MemberStats.fromJson(data);
  }

  Future<MemberItem> getMember(int memberId) async {
    final response = await _dio.get<Map<String, dynamic>>('/members/$memberId');
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to load member detail',
    );
    return MemberItem.fromJson(data);
  }

  Future<MemberItem> createMember(Map<String, dynamic> payload) async {
    final response = await _dio.post<Map<String, dynamic>>('/members/', data: payload);
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to create member',
    );
    return MemberItem.fromJson(data);
  }

  Future<MemberItem> updateMember(
    int memberId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.put<Map<String, dynamic>>('/members/$memberId', data: payload);
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to update member',
    );
    return MemberItem.fromJson(data);
  }

  Future<void> deleteMember(int memberId) async {
    final response = await _dio.delete<Map<String, dynamic>>('/members/$memberId');
    _ensureSuccess(response.data, 'Failed to delete member');
  }

  Future<void> changePassword({
    required int memberId,
    String? oldPassword,
    required String newPassword,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/members/$memberId/change-password',
      data: <String, dynamic>{
        'old_password': (oldPassword != null && oldPassword.trim().isNotEmpty)
            ? oldPassword.trim()
            : '000000',
        'new_password': newPassword,
      },
    );
    _ensureSuccess(response.data, 'Failed to change password');
  }
}

String? _normalizeText(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}

Map<String, dynamic> _extractResponseData(
  Map<String, dynamic>? response, {
  required String fallbackMessage,
}) {
  if (response == null) {
    throw Exception(fallbackMessage);
  }

  if (response['success'] != true) {
    throw Exception(_extractResponseMessage(response, fallbackMessage));
  }

  final data = response['data'];
  if (data is Map<String, dynamic>) {
    return data;
  }
  if (data is Map) {
    return Map<String, dynamic>.from(data);
  }

  throw Exception(fallbackMessage);
}

void _ensureSuccess(Map<String, dynamic>? response, String fallbackMessage) {
  if (response == null) {
    return;
  }
  if (response['success'] == false) {
    throw Exception(_extractResponseMessage(response, fallbackMessage));
  }
}

String _extractResponseMessage(
  Map<String, dynamic>? response,
  String fallbackMessage,
) {
  if (response == null) {
    return fallbackMessage;
  }
  return response['message'] as String? ?? fallbackMessage;
}

int _readInt(Object? value) {
  if (value is int) {
    return value;
  }
  if (value is num) {
    return value.toInt();
  }
  return 0;
}

Map<String, int> _readIntMap(Object? value) {
  if (value is! Map) {
    return const {};
  }

  return value.map<String, int>((key, raw) {
    return MapEntry(key.toString(), _readInt(raw));
  });
}
