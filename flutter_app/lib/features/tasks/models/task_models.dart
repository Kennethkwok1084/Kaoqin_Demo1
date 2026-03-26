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
