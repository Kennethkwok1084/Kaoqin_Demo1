import 'package:json_annotation/json_annotation.dart';

part 'dashboard_models.g.dart';

@JsonSerializable()
class TrendData {
  final double value;
  final String direction;

  const TrendData({
    required this.value,
    required this.direction,
  });

  factory TrendData.fromJson(Map<String, dynamic> json) => _$TrendDataFromJson(json);
  Map<String, dynamic> toJson() => _$TrendDataToJson(this);
}

@JsonSerializable()
class MetricsData {
  @JsonKey(name: 'totalTasks')
  final int totalTasks;
  @JsonKey(name: 'inProgress')
  final int inProgress;
  final int pending;
  @JsonKey(name: 'completedThisMonth')
  final int completedThisMonth;
  @JsonKey(name: 'systemStatus')
  final String systemStatus;

  const MetricsData({
    required this.totalTasks,
    required this.inProgress,
    required this.pending,
    required this.completedThisMonth,
    required this.systemStatus,
  });

  factory MetricsData.fromJson(Map<String, dynamic> json) => _$MetricsDataFromJson(json);
  Map<String, dynamic> toJson() => _$MetricsDataToJson(this);
}

@JsonSerializable()
class TrendsData {
  @JsonKey(name: 'totalTasksTrend')
  final TrendData totalTasksTrend;
  @JsonKey(name: 'inProgressTrend')
  final TrendData inProgressTrend;
  @JsonKey(name: 'pendingTrend')
  final TrendData pendingTrend;
  @JsonKey(name: 'completedTrend')
  final TrendData completedTrend;

  const TrendsData({
    required this.totalTasksTrend,
    required this.inProgressTrend,
    required this.pendingTrend,
    required this.completedTrend,
  });

  factory TrendsData.fromJson(Map<String, dynamic> json) => _$TrendsDataFromJson(json);
  Map<String, dynamic> toJson() => _$TrendsDataToJson(this);
}

@JsonSerializable()
class SystemInfo {
  @JsonKey(name: 'onlineUsers')
  final int onlineUsers;
  @JsonKey(name: 'lastDataSync')
  final String lastDataSync;
  @JsonKey(name: 'systemUptime')
  final String systemUptime;

  const SystemInfo({
    required this.onlineUsers,
    required this.lastDataSync,
    required this.systemUptime,
  });

  factory SystemInfo.fromJson(Map<String, dynamic> json) => _$SystemInfoFromJson(json);
  Map<String, dynamic> toJson() => _$SystemInfoToJson(this);
}

@JsonSerializable()
class DashboardOverviewResponse {
  final MetricsData metrics;
  final TrendsData trends;
  final SystemInfo systemInfo;

  const DashboardOverviewResponse({
    required this.metrics,
    required this.trends,
    required this.systemInfo,
  });

  factory DashboardOverviewResponse.fromJson(Map<String, dynamic> json) => _$DashboardOverviewResponseFromJson(json);
  Map<String, dynamic> toJson() => _$DashboardOverviewResponseToJson(this);
}
