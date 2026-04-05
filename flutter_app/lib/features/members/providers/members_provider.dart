import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
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

final memberImportTemplateProvider = FutureProvider<MemberImportTemplate>((ref) async {
  final service = ref.watch(membersCommandProvider);
  return service.getImportTemplate();
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


class MemberImportTemplate {
  const MemberImportTemplate({
    required this.filename,
    required this.supportedFileTypes,
    required this.maxFileSizeMb,
    required this.columns,
  });

  final String filename;
  final List<String> supportedFileTypes;
  final int maxFileSizeMb;
  final List<MemberImportTemplateColumn> columns;

  static const defaultTemplate = MemberImportTemplate(
    filename: 'member_import_template.xlsx',
    supportedFileTypes: ['.xlsx', '.xls', '.csv'],
    maxFileSizeMb: 10,
    columns: [
      MemberImportTemplateColumn(name: '姓名', field: 'name', required: true, example: '张三'),
      MemberImportTemplateColumn(name: '学号', field: 'student_id', required: false, example: '2023001'),
      MemberImportTemplateColumn(name: '手机号', field: 'phone', required: false, example: '13800138000'),
      MemberImportTemplateColumn(name: '部门', field: 'department', required: false, example: '信息化建设处'),
      MemberImportTemplateColumn(name: '班级', field: 'class_name', required: true, example: '计算机1班'),
      MemberImportTemplateColumn(name: '角色', field: 'role', required: false, example: 'member'),
      MemberImportTemplateColumn(name: '小组ID', field: 'group_id', required: false, example: '1'),
    ],
  );
}

class MemberImportTemplateColumn {
  const MemberImportTemplateColumn({
    required this.name,
    required this.field,
    required this.required,
    this.example,
  });

  final String name;
  final String field;
  final bool required;
  final String? example;
}

class MemberImportPreview {
  const MemberImportPreview({
    required this.totalRows,
    required this.validRows,
    required this.invalidRows,
    required this.emptyRows,
    required this.previewData,
    required this.errors,
  });

  final int totalRows;
  final int validRows;
  final int invalidRows;
  final int emptyRows;
  final List<Map<String, dynamic>> previewData;
  final List<String> errors;

  factory MemberImportPreview.fromJson(Map<String, dynamic> json) {
    return MemberImportPreview(
      totalRows: _readInt(json['total_rows']),
      validRows: _readInt(json['valid_rows']),
      invalidRows: _readInt(json['invalid_rows']),
      emptyRows: _readInt(json['empty_rows']),
      previewData: _readMapList(json['preview_data']),
      errors: _readStringList(json['errors']),
    );
  }
}

class MemberImportResult {
  const MemberImportResult({
    required this.totalProcessed,
    required this.successfulImports,
    required this.failedImports,
    required this.skippedDuplicates,
    required this.errors,
    this.fileSummary,
  });

  final int totalProcessed;
  final int successfulImports;
  final int failedImports;
  final int skippedDuplicates;
  final List<String> errors;
  final MemberImportFileSummary? fileSummary;

  factory MemberImportResult.fromJson(Map<String, dynamic> json) {
    final rawSummary = json['file_summary'];
    return MemberImportResult(
      totalProcessed: _readInt(json['total_processed']),
      successfulImports: _readInt(json['successful_imports']),
      failedImports: _readInt(json['failed_imports']),
      skippedDuplicates: _readInt(json['skipped_duplicates']),
      errors: _readStringList(json['errors']),
      fileSummary: rawSummary is Map
          ? MemberImportFileSummary.fromJson(Map<String, dynamic>.from(rawSummary))
          : null,
    );
  }
}

class MemberImportFileSummary {
  const MemberImportFileSummary({
    required this.totalRows,
    required this.validRows,
    required this.invalidRows,
    required this.emptyRows,
  });

  final int totalRows;
  final int validRows;
  final int invalidRows;
  final int emptyRows;

  factory MemberImportFileSummary.fromJson(Map<String, dynamic> json) {
    return MemberImportFileSummary(
      totalRows: _readInt(json['total_rows']),
      validRows: _readInt(json['valid_rows']),
      invalidRows: _readInt(json['invalid_rows']),
      emptyRows: _readInt(json['empty_rows']),
    );
  }
}

class DownloadedTemplateFile {
  const DownloadedTemplateFile({
    required this.filename,
    required this.bytes,
  });

  final String filename;
  final List<int> bytes;
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

  Future<MemberImportTemplate> getImportTemplate() async {
    return MemberImportTemplate.defaultTemplate;
  }

  Future<DownloadedTemplateFile> downloadImportTemplate() async {
    final response = await _dio.get<dynamic>(
      '/members/import-template',
      options: Options(responseType: ResponseType.bytes),
    );

    final data = response.data;
    final filename = _extractDownloadFilename(
      response.headers.value('content-disposition'),
    );
    if (data is List<int>) {
      return DownloadedTemplateFile(filename: filename, bytes: data);
    }
    if (data is List) {
      return DownloadedTemplateFile(filename: filename, bytes: data.cast<int>());
    }
    throw Exception('模板下载响应不是有效文件流');
  }

  Future<MemberImportPreview> previewExcelImport({
    required XFile file,
    bool skipDuplicates = true,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/members/import-excel',
      options: Options(contentType: 'multipart/form-data'),
      data: await _buildImportFormData(
        file: file,
        skipDuplicates: skipDuplicates,
        dryRun: true,
      ),
    );
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to validate import file',
    );
    return MemberImportPreview.fromJson(data);
  }

  Future<MemberImportResult> importExcel({
    required XFile file,
    bool skipDuplicates = true,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/members/import-excel',
      options: Options(contentType: 'multipart/form-data'),
      data: await _buildImportFormData(
        file: file,
        skipDuplicates: skipDuplicates,
        dryRun: false,
      ),
    );
    final data = _extractResponseData(
      response.data,
      fallbackMessage: 'Failed to import members',
    );
    return MemberImportResult.fromJson(data);
  }

  Future<FormData> _buildImportFormData({
    required XFile file,
    required bool skipDuplicates,
    required bool dryRun,
  }) async {
    final bytes = await file.readAsBytes();
    return FormData.fromMap(
      <String, dynamic>{
        'file': MultipartFile.fromBytes(bytes, filename: file.name),
        'skip_duplicates': skipDuplicates,
        'dry_run': dryRun,
      },
    );
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

List<String> _readStringList(Object? value) {
  if (value is! List) return const [];
  return value.map((item) => item.toString()).toList(growable: false);
}

List<Map<String, dynamic>> _readMapList(Object? value) {
  if (value is! List) return const [];
  return value
      .whereType<Map>()
      .map((item) => Map<String, dynamic>.from(item))
      .toList(growable: false);
}

String _extractDownloadFilename(String? contentDisposition) {
  if (contentDisposition == null || contentDisposition.isEmpty) {
    return MemberImportTemplate.defaultTemplate.filename;
  }

  final utf8Match = RegExp(
    r"filename\*=UTF-8''([^;]+)",
    caseSensitive: false,
  ).firstMatch(contentDisposition);
  if (utf8Match != null) {
    return Uri.decodeFull(utf8Match.group(1)!);
  }

  final plainMatch = RegExp(
    r'filename="?([^";]+)"?',
    caseSensitive: false,
  ).firstMatch(contentDisposition);
  if (plainMatch != null) {
    return plainMatch.group(1)!;
  }

  return MemberImportTemplate.defaultTemplate.filename;
}


