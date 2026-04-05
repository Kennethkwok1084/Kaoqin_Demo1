enum TaskWorkspaceType {
  repair,
  monitoring,
  assistance;

  String get apiValue => switch (this) {
        TaskWorkspaceType.repair => 'repair',
        TaskWorkspaceType.monitoring => 'monitoring',
        TaskWorkspaceType.assistance => 'assistance',
      };
}

class PaginatedData<T> {
  const PaginatedData({
    required this.items,
    required this.total,
    required this.page,
    required this.size,
    required this.pages,
  });

  final List<T> items;
  final int total;
  final int page;
  final int size;
  final int pages;

  factory PaginatedData.fromJson(
    Map<String, dynamic> json,
    T Function(Map<String, dynamic> json) fromJsonT,
  ) {
    final rawItems = json['items'] as List<dynamic>? ?? const [];
    return PaginatedData<T>(
      items: rawItems
          .whereType<Map>()
          .map((item) => fromJsonT(Map<String, dynamic>.from(item)))
          .toList(growable: false),
      total: _readInt(json['total']),
      page: _readInt(json['page'], fallback: 1),
      size: _readInt(json['size'] ?? json['pageSize'] ?? json['page_size'], fallback: 20),
      pages: _readInt(json['pages'] ?? json['total_pages'], fallback: 1),
    );
  }
}

class TaskItem {
  const TaskItem({
    required this.id,
    required this.type,
    required this.title,
    this.description,
    this.location,
    this.status,
    this.priority,
    this.memberId,
    this.assigneeName,
    this.contactPerson,
    this.contactPhone,
    this.createdAt,
    this.dueDate,
    this.workMinutes,
    this.memberName,
    this.startTime,
    this.endTime,
    this.assistedDepartment,
    this.assistedPerson,
    this.monitoringType,
  });

  final int id;
  final String type;
  final String title;
  final String? description;
  final String? location;
  final String? status;
  final String? priority;
  final int? memberId;
  final String? assigneeName;
  final String? contactPerson;
  final String? contactPhone;
  final String? createdAt;
  final String? dueDate;
  final int? workMinutes;
  final String? memberName;
  final String? startTime;
  final String? endTime;
  final String? assistedDepartment;
  final String? assistedPerson;
  final String? monitoringType;

  factory TaskItem.fromJson(
    Map<String, dynamic> json, {
    required TaskWorkspaceType fallbackType,
  }) {
    final resolvedType = _readString(
          json['type'] ?? json['task_type'],
        ) ??
        fallbackType.apiValue;

    return TaskItem(
      id: _readInt(json['id']),
      type: resolvedType,
      title: _readString(json['title']) ?? '',
      description: _readString(json['description']),
      location: _readString(json['location']),
      status: _readString(json['status']),
      priority: _readString(json['priority']),
      memberId: _readNullableInt(json['member_id'] ?? json['memberId']),
      assigneeName: _readString(
        json['assigneeName'] ?? json['member_name'] ?? json['memberName'],
      ),
      contactPerson: _readString(
        json['contactPerson'] ?? json['contact_person'],
      ),
      contactPhone: _readString(
        json['contactPhone'] ?? json['contact_phone'],
      ),
      createdAt: _readString(json['createdAt'] ?? json['created_at']),
      dueDate: _readString(
        json['dueDate'] ??
            json['due_date'] ??
            json['completionTime'] ??
            json['completion_time'],
      ),
      workMinutes: _readNullableInt(json['work_minutes'] ?? json['workMinutes']),
      memberName: _readString(json['member_name'] ?? json['memberName']),
      startTime: _readString(json['start_time'] ?? json['startTime']),
      endTime: _readString(json['end_time'] ?? json['endTime']),
      assistedDepartment: _readString(
        json['assisted_department'] ?? json['assistedDepartment'],
      ),
      assistedPerson: _readString(
        json['assisted_person'] ?? json['assistedPerson'],
      ),
      monitoringType: _readString(
        json['monitoring_type'] ?? json['monitoringType'],
      ),
    );
  }
}

class TaskAssigneeOption {
  const TaskAssigneeOption({
    required this.id,
    required this.name,
    this.studentId,
  });

  final int id;
  final String name;
  final String? studentId;

  factory TaskAssigneeOption.fromJson(Map<String, dynamic> json) {
    return TaskAssigneeOption(
      id: _readInt(json['id']),
      name: _readString(json['name'] ?? json['username']) ?? '',
      studentId: _readString(json['student_id'] ?? json['studentId']),
    );
  }
}

class RepairImportTemplateField {
  const RepairImportTemplateField({
    required this.field,
    required this.description,
    required this.required,
    this.example,
  });

  final String field;
  final String description;
  final bool required;
  final String? example;

  factory RepairImportTemplateField.fromJson(Map<String, dynamic> json) {
    return RepairImportTemplateField(
      field: _readString(json['field']) ?? '',
      description: _readString(json['description']) ?? '',
      required: _readNullableBool(json['required']) ?? false,
      example: _readString(json['example']),
    );
  }
}

class RepairImportTemplate {
  const RepairImportTemplate({
    required this.fields,
    required this.rules,
  });

  final List<RepairImportTemplateField> fields;
  final Map<String, dynamic> rules;

  factory RepairImportTemplate.fromJson(Map<String, dynamic> json) {
    final rawFields = json['template_fields'] as List<dynamic>? ?? const [];
    return RepairImportTemplate(
      fields: rawFields
          .whereType<Map>()
          .map((item) => RepairImportTemplateField.fromJson(Map<String, dynamic>.from(item)))
          .toList(growable: false),
      rules: _mapOrEmpty(json['import_rules']),
    );
  }
}

class RepairImportPreview {
  const RepairImportPreview({
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

  factory RepairImportPreview.fromJson(Map<String, dynamic> json) {
    final rawPreview = json['preview_data'] as List<dynamic>? ?? const [];
    final rawErrors = json['errors'] as List<dynamic>? ?? const [];
    return RepairImportPreview(
      totalRows: _readInt(json['total_rows']),
      validRows: _readInt(json['valid_rows']),
      invalidRows: _readInt(json['invalid_rows']),
      emptyRows: _readInt(json['empty_rows']),
      previewData: rawPreview
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList(growable: false),
      errors: rawErrors.map((item) => item.toString()).toList(growable: false),
    );
  }
}

class RepairImportResult {
  const RepairImportResult({
    required this.totalRows,
    required this.validRows,
    required this.invalidRows,
    required this.emptyRows,
    required this.successfulImports,
    required this.failedImports,
    required this.skippedDuplicates,
    required this.errors,
  });

  final int totalRows;
  final int validRows;
  final int invalidRows;
  final int emptyRows;
  final int successfulImports;
  final int failedImports;
  final int skippedDuplicates;
  final List<String> errors;

  factory RepairImportResult.fromJson(Map<String, dynamic> json) {
    final rawErrors = json['errors'] as List<dynamic>? ?? const [];
    return RepairImportResult(
      totalRows: _readInt(json['total_rows']),
      validRows: _readInt(json['valid_rows']),
      invalidRows: _readInt(json['invalid_rows']),
      emptyRows: _readInt(json['empty_rows']),
      successfulImports: _readInt(json['successful_imports']),
      failedImports: _readInt(json['failed_imports']),
      skippedDuplicates: _readInt(json['skipped_duplicates']),
      errors: rawErrors.map((item) => item.toString()).toList(growable: false),
    );
  }
}

class TaskStats {
  const TaskStats({
    required this.total,
    required this.pending,
    required this.inProgress,
    required this.completed,
    this.todayCreated,
    this.todayCompleted,
    this.personalAssigned,
    this.personalPending,
    this.completionRate,
  });

  final int total;
  final int pending;
  final int inProgress;
  final int completed;
  final int? todayCreated;
  final int? todayCompleted;
  final int? personalAssigned;
  final int? personalPending;
  final double? completionRate;

  factory TaskStats.fromJson(Map<String, dynamic> json) {
    final overview = _mapOrEmpty(json['overview']);
    final today = _mapOrEmpty(json['today']);
    final personal = _mapOrEmpty(json['personal']);

    return TaskStats(
      total: _readInt(overview['total']),
      pending: _readInt(overview['pending']),
      inProgress: _readInt(overview['in_progress']),
      completed: _readInt(overview['completed']),
      todayCreated: _readNullableInt(today['created']),
      todayCompleted: _readNullableInt(today['completed']),
      personalAssigned: _readNullableInt(personal['assigned']),
      personalPending: _readNullableInt(personal['pending']),
      completionRate: _readNullableDouble(json['completion_rate']),
    );
  }

  static const empty = TaskStats(
    total: 0,
    pending: 0,
    inProgress: 0,
    completed: 0,
  );
}

class TaskTagItem {
  const TaskTagItem({
    required this.id,
    required this.name,
    this.workMinutesModifier,
    this.tagType,
  });

  final int id;
  final String name;
  final int? workMinutesModifier;
  final String? tagType;

  factory TaskTagItem.fromJson(Map<String, dynamic> json) {
    return TaskTagItem(
      id: _readInt(json['id']),
      name: _readString(json['name']) ?? '',
      workMinutesModifier: _readNullableInt(
        json['work_minutes_modifier'] ?? json['workMinutesModifier'],
      ),
      tagType: _readString(json['tag_type'] ?? json['tagType']),
    );
  }
}

class TaskDetailItem {
  const TaskDetailItem({
    required this.id,
    required this.taskId,
    required this.title,
    this.description,
    this.status,
    this.taskType,
    this.priority,
    this.category,
    this.location,
    this.reportTime,
    this.responseTime,
    this.completionTime,
    this.workMinutes,
    this.baseWorkMinutes,
    this.rating,
    this.feedback,
    this.reporterName,
    this.reporterContact,
    this.memberId,
    this.memberName,
    this.memberStudentId,
    this.isOverdueResponse,
    this.isOverdueCompletion,
    this.isPositiveReview,
    this.isNegativeReview,
    this.isNonDefaultPositiveReview,
    this.tags = const [],
    this.workHourBreakdown = const {},
    this.createdAt,
    this.updatedAt,
  });

  final int id;
  final String taskId;
  final String title;
  final String? description;
  final String? status;
  final String? taskType;
  final String? priority;
  final String? category;
  final String? location;
  final String? reportTime;
  final String? responseTime;
  final String? completionTime;
  final int? workMinutes;
  final int? baseWorkMinutes;
  final int? rating;
  final String? feedback;
  final String? reporterName;
  final String? reporterContact;
  final int? memberId;
  final String? memberName;
  final String? memberStudentId;
  final bool? isOverdueResponse;
  final bool? isOverdueCompletion;
  final bool? isPositiveReview;
  final bool? isNegativeReview;
  final bool? isNonDefaultPositiveReview;
  final List<TaskTagItem> tags;
  final Map<String, dynamic> workHourBreakdown;
  final String? createdAt;
  final String? updatedAt;

  factory TaskDetailItem.fromJson(Map<String, dynamic> json) {
    final tags = (json['tags'] as List<dynamic>? ?? const [])
        .whereType<Map>()
        .map((item) => TaskTagItem.fromJson(Map<String, dynamic>.from(item)))
        .toList(growable: false);

    return TaskDetailItem(
      id: _readInt(json['id']),
      taskId: _readString(json['task_id'] ?? json['taskId']) ?? '',
      title: _readString(json['title']) ?? '',
      description: _readString(json['description']),
      status: _readString(json['status']),
      taskType: _readString(json['task_type'] ?? json['type'] ?? json['taskType']),
      priority: _readString(json['priority']),
      category: _readString(json['category']),
      location: _readString(json['location']),
      reportTime: _readString(json['report_time'] ?? json['reportTime']),
      responseTime: _readString(json['response_time'] ?? json['responseTime']),
      completionTime: _readString(
        json['completion_time'] ??
            json['completed_at'] ??
            json['completedAt'] ??
            json['completionTime'],
      ),
      workMinutes: _readNullableInt(json['work_minutes'] ?? json['workMinutes']),
      baseWorkMinutes: _readNullableInt(
        json['base_work_minutes'] ?? json['baseWorkMinutes'],
      ),
      rating: _readNullableInt(json['rating']),
      feedback: _readString(json['feedback'] ?? json['review_comment']),
      reporterName: _readString(json['reporter_name'] ?? json['reporterName']),
      reporterContact: _readString(
        json['reporter_contact'] ?? json['reporterContact'],
      ),
      memberId: _readNullableInt(json['member_id'] ?? json['memberId']),
      memberName: _readString(json['member_name'] ?? json['memberName']),
      memberStudentId: _readString(
        json['member_student_id'] ?? json['memberStudentId'],
      ),
      isOverdueResponse: _readNullableBool(
        json['is_overdue_response'] ?? json['isOverdueResponse'],
      ),
      isOverdueCompletion: _readNullableBool(
        json['is_overdue_completion'] ?? json['isOverdueCompletion'],
      ),
      isPositiveReview: _readNullableBool(
        json['is_positive_review'] ?? json['isPositiveReview'],
      ),
      isNegativeReview: _readNullableBool(
        json['is_negative_review'] ?? json['isNegativeReview'],
      ),
      isNonDefaultPositiveReview: _readNullableBool(
        json['is_non_default_positive_review'] ?? json['isNonDefaultPositiveReview'],
      ),
      tags: tags,
      workHourBreakdown: _mapOrEmpty(
        json['work_hour_breakdown'] ?? json['workHourBreakdown'],
      ),
      createdAt: _readString(json['created_at'] ?? json['createdAt']),
      updatedAt: _readString(json['updated_at'] ?? json['updatedAt']),
    );
  }
}

class RepairTaskFormData {
  const RepairTaskFormData({
    required this.title,
    this.description,
    this.location,
    this.reporterName,
    this.reporterContact,
    this.assignedTo,
    this.priority,
  });

  final String title;
  final String? description;
  final String? location;
  final String? reporterName;
  final String? reporterContact;
  final int? assignedTo;
  final String? priority;

  Map<String, dynamic> toCreatePayload() {
    return <String, dynamic>{
      'title': title.trim(),
      if (_clean(description) != null) 'description': _clean(description),
      if (_clean(location) != null) 'location': _clean(location),
      if (_clean(reporterName) != null) 'reporter_name': _clean(reporterName),
      if (_clean(reporterContact) != null) 'reporter_contact': _clean(reporterContact),
      if (assignedTo != null) 'assigned_to': assignedTo,
    };
  }

  Map<String, dynamic> toUpdatePayload() {
    return <String, dynamic>{
      'title': title.trim(),
      if (_clean(description) != null) 'description': _clean(description),
      if (assignedTo != null) 'assigned_to': assignedTo,
      if (_clean(priority) != null) 'priority': _clean(priority),
    };
  }
}

int _readInt(Object? value, {int fallback = 0}) => _readNullableInt(value) ?? fallback;

int? _readNullableInt(Object? value) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  if (value is String) return int.tryParse(value);
  return null;
}

double? _readNullableDouble(Object? value) {
  if (value is double) return value;
  if (value is num) return value.toDouble();
  if (value is String) return double.tryParse(value);
  return null;
}

bool? _readNullableBool(Object? value) {
  if (value is bool) return value;
  if (value is String) {
    if (value == 'true') return true;
    if (value == 'false') return false;
  }
  return null;
}

String? _readString(Object? value) {
  if (value == null) return null;
  final text = value.toString().trim();
  return text.isEmpty ? null : text;
}

Map<String, dynamic> _mapOrEmpty(Object? value) {
  if (value is Map<String, dynamic>) {
    return value;
  }
  if (value is Map) {
    return Map<String, dynamic>.from(value);
  }
  return const {};
}

String? _clean(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}
