import 'package:json_annotation/json_annotation.dart';

part 'member_models.g.dart';

@JsonSerializable()
class MemberItem {
  final int id;
  final String username;
  final String? name;
  @JsonKey(name: 'student_id')
  final String? studentId;
  final String? phone;
  final String? department;
  @JsonKey(name: 'class_name')
  final String? className;
  final String? role;
  
  @JsonKey(name: 'is_active')
  final bool? isActive;
  
  @JsonKey(name: 'status_display')
  final String? statusDisplay;
  
  @JsonKey(name: 'join_date')
  final String? joinDate;

  const MemberItem({
    required this.id,
    required this.username,
    this.name,
    this.studentId,
    this.phone,
    this.department,
    this.className,
    this.role,
    this.isActive,
    this.statusDisplay,
    this.joinDate,
  });

  factory MemberItem.fromJson(Map<String, dynamic> json) => _$MemberItemFromJson(json);
  Map<String, dynamic> toJson() => _$MemberItemToJson(this);
}
