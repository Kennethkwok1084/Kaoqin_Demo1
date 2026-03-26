import 'package:json_annotation/json_annotation.dart';

part 'paginated_data.g.dart';

@JsonSerializable(genericArgumentFactories: true)
class PaginatedData<T> {
  final List<T> items;
  final int total;
  final int page;

  @JsonKey(name: 'page_size')
  final int? pageSize;

  @JsonKey(name: 'size')
  final int? size;

  @JsonKey(name: 'total_pages')
  final int? totalPages;

  PaginatedData({
    required this.items,
    required this.total,
    required this.page,
    this.pageSize,
    this.size,
    this.totalPages,
  });

  factory PaginatedData.fromJson(
    Map<String, dynamic> json,
    T Function(Object? json) fromJsonT,
  ) =>
      _$PaginatedDataFromJson(json, fromJsonT);

  Map<String, dynamic> toJson(Object? Function(T value) toJsonT) =>
      _$PaginatedDataToJson(this, toJsonT);
}
