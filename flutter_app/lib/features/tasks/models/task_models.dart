import 'package:json_annotation/json_annotation.dart';

part 'task_models.g.dart';

@JsonSerializable(genericArgumentFactories: true)
class PaginatedData<T> {
  final List<T> items;
  final int total;
  final int page;
  final int size;
  final int pages;

  const PaginatedData({
    required this.items,
    required this.total,
    required this.page,
    required this.size,
    required this.pages,
  });

  factory PaginatedData.fromJson(
    Map<String, dynamic> json,
    T Function(Object? json) fromJsonT,
  ) =>
      _$PaginatedDataFromJson(json, fromJsonT);
}

@JsonSerializable()
class TaskItem {
  final int id;
  final String title;
  final String? description;
  final String? location;
  final String? status;
  final String? priority;
  
  @JsonKey(name: 'assigneeName')
  final String? assigneeName;

  @JsonKey(name: 'contactPerson')
  final String? contactPerson;

  @JsonKey(name: 'createdAt')
  final String? createdAt;
  
  @JsonKey(name: 'dueDate')
  final String? dueDate;

  const TaskItem({
    required this.id,
    required this.title,
    this.description,
    this.location,
    this.status,
    this.priority,
    this.assigneeName,
    this.contactPerson,
    this.createdAt,
    this.dueDate,
  });

  factory TaskItem.fromJson(Map<String, dynamic> json) => _$TaskItemFromJson(json);
  Map<String, dynamic> toJson() => _$TaskItemToJson(this);
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
      id: json['id'] as int? ?? 0,
      name: json['name'] as String? ?? '',
      workMinutesModifier: json['work_minutes_modifier'] as int?,
      tagType: json['tag_type'] as String?,
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
        .toList();

    return TaskDetailItem(
      id: json['id'] as int? ?? 0,
      taskId: json['task_id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String?,
      status: json['status'] as String?,
      taskType: json['task_type'] as String?,
      priority: json['priority'] as String?,
      category: json['category'] as String?,
      location: json['location'] as String?,
      reportTime: _stringOrNull(json['report_time']),
      responseTime: _stringOrNull(json['response_time']),
      completionTime: _stringOrNull(json['completion_time']),
      workMinutes: json['work_minutes'] as int?,
      baseWorkMinutes: json['base_work_minutes'] as int?,
      rating: json['rating'] as int?,
      feedback: json['feedback'] as String?,
      reporterName: json['reporter_name'] as String?,
      reporterContact: json['reporter_contact'] as String?,
      memberId: json['member_id'] as int?,
      memberName: json['member_name'] as String?,
      memberStudentId: json['member_student_id'] as String?,
      isOverdueResponse: json['is_overdue_response'] as bool?,
      isOverdueCompletion: json['is_overdue_completion'] as bool?,
      isPositiveReview: json['is_positive_review'] as bool?,
      isNegativeReview: json['is_negative_review'] as bool?,
      isNonDefaultPositiveReview: json['is_non_default_positive_review'] as bool?,
      tags: tags,
      workHourBreakdown: _mapOrEmpty(json['work_hour_breakdown']),
      createdAt: _stringOrNull(json['created_at']),
      updatedAt: _stringOrNull(json['updated_at']),
    );
  }
}

String? _stringOrNull(Object? value) {
  if (value == null) {
    return null;
  }
  return value.toString();
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
