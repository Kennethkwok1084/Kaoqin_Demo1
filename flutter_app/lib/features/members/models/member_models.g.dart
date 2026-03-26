// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'member_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MemberItem _$MemberItemFromJson(Map<String, dynamic> json) => MemberItem(
      id: (json['id'] as num).toInt(),
      username: json['username'] as String,
      name: json['name'] as String?,
      studentId: json['student_id'] as String?,
      phone: json['phone'] as String?,
      department: json['department'] as String?,
      className: json['class_name'] as String?,
      role: json['role'] as String?,
      isActive: json['is_active'] as bool?,
      statusDisplay: json['status_display'] as String?,
      joinDate: json['join_date'] as String?,
    );

Map<String, dynamic> _$MemberItemToJson(MemberItem instance) =>
    <String, dynamic>{
      'id': instance.id,
      'username': instance.username,
      'name': instance.name,
      'student_id': instance.studentId,
      'phone': instance.phone,
      'department': instance.department,
      'class_name': instance.className,
      'role': instance.role,
      'is_active': instance.isActive,
      'status_display': instance.statusDisplay,
      'join_date': instance.joinDate,
    };
