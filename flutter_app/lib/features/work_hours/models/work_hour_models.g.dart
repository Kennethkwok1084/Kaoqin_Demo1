// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'work_hour_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

WorkHourRecord _$WorkHourRecordFromJson(Map<String, dynamic> json) =>
    WorkHourRecord(
      id: (json['id'] as num).toInt(),
      memberId: (json['member_id'] as num).toInt(),
      memberName: json['member_name'] as String?,
      workDate: json['work_date'] as String?,
      workHours: (json['work_hours'] as num?)?.toDouble(),
      workMinutes: (json['work_minutes'] as num?)?.toInt(),
      taskType: json['task_type'] as String?,
      title: json['title'] as String?,
      taskCategory: json['task_category'] as String?,
      rating: (json['rating'] as num?)?.toInt(),
      source: json['source'] as String?,
    );

Map<String, dynamic> _$WorkHourRecordToJson(WorkHourRecord instance) =>
    <String, dynamic>{
      'id': instance.id,
      'member_id': instance.memberId,
      'member_name': instance.memberName,
      'work_date': instance.workDate,
      'work_hours': instance.workHours,
      'work_minutes': instance.workMinutes,
      'task_type': instance.taskType,
      'title': instance.title,
      'task_category': instance.taskCategory,
      'rating': instance.rating,
      'source': instance.source,
    };
