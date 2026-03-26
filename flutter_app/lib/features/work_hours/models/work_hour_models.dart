import 'package:json_annotation/json_annotation.dart';

part 'work_hour_models.g.dart';

@JsonSerializable()
class WorkHourRecord {
  final int id;
  @JsonKey(name: 'member_id')
  final int memberId;
  @JsonKey(name: 'member_name')
  final String? memberName;
  @JsonKey(name: 'work_date')
  final String? workDate;
  @JsonKey(name: 'work_hours')
  final double? workHours;
  @JsonKey(name: 'work_minutes')
  final int? workMinutes;

  @JsonKey(name: 'task_type')
  final String? taskType;
  @JsonKey(name: 'title')
  final String? title;
  @JsonKey(name: 'task_category')
  final String? taskCategory;
  @JsonKey(name: 'rating')
  final int? rating;
  @JsonKey(name: 'source')
  final String? source;

  WorkHourRecord({
    required this.id,
    required this.memberId,
    this.memberName,
    this.workDate,
    this.workHours,
    this.workMinutes,
    this.taskType,
    this.title,
    this.taskCategory,
    this.rating,
    this.source,
  });

  factory WorkHourRecord.fromJson(Map<String, dynamic> json) =>
      _$WorkHourRecordFromJson(json);
  Map<String, dynamic> toJson() => _$WorkHourRecordToJson(this);
}
