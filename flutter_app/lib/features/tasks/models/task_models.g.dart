// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'task_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PaginatedData<T> _$PaginatedDataFromJson<T>(
  Map<String, dynamic> json,
  T Function(Object? json) fromJsonT,
) =>
    PaginatedData<T>(
      items: (json['items'] as List<dynamic>).map(fromJsonT).toList(),
      total: (json['total'] as num).toInt(),
      page: (json['page'] as num).toInt(),
      size: (json['size'] as num).toInt(),
      pages: (json['pages'] as num).toInt(),
    );

Map<String, dynamic> _$PaginatedDataToJson<T>(
  PaginatedData<T> instance,
  Object? Function(T value) toJsonT,
) =>
    <String, dynamic>{
      'items': instance.items.map(toJsonT).toList(),
      'total': instance.total,
      'page': instance.page,
      'size': instance.size,
      'pages': instance.pages,
    };

TaskItem _$TaskItemFromJson(Map<String, dynamic> json) => TaskItem(
      id: (json['id'] as num).toInt(),
      title: json['title'] as String,
      description: json['description'] as String?,
      location: json['location'] as String?,
      status: json['status'] as String?,
      priority: json['priority'] as String?,
      assigneeName: json['assigneeName'] as String?,
      contactPerson: json['contactPerson'] as String?,
      createdAt: json['createdAt'] as String?,
      dueDate: json['dueDate'] as String?,
    );

Map<String, dynamic> _$TaskItemToJson(TaskItem instance) => <String, dynamic>{
      'id': instance.id,
      'title': instance.title,
      'description': instance.description,
      'location': instance.location,
      'status': instance.status,
      'priority': instance.priority,
      'assigneeName': instance.assigneeName,
      'contactPerson': instance.contactPerson,
      'createdAt': instance.createdAt,
      'dueDate': instance.dueDate,
    };
