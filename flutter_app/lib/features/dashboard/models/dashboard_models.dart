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

class DashboardTaskSummaryItem {
  const DashboardTaskSummaryItem({
    required this.id,
    required this.title,
    required this.status,
    required this.priority,
    required this.location,
    this.createdAt,
    this.dueDate,
  });

  final int id;
  final String title;
  final String status;
  final String priority;
  final String location;
  final String? createdAt;
  final String? dueDate;

  factory DashboardTaskSummaryItem.fromJson(Map<String, dynamic> json) {
    return DashboardTaskSummaryItem(
      id: json['id'] as int? ?? 0,
      title: json['title'] as String? ?? '',
      status: json['status'] as String? ?? '',
      priority: json['priority'] as String? ?? '',
      location: json['location'] as String? ?? '',
      createdAt: json['createdAt'] as String?,
      dueDate: json['dueDate'] as String?,
    );
  }
}

class DashboardTaskStatsData {
  const DashboardTaskStatsData({
    required this.totalAssigned,
    required this.pending,
    required this.inProgress,
    required this.completed,
  });

  final int totalAssigned;
  final int pending;
  final int inProgress;
  final int completed;

  factory DashboardTaskStatsData.fromJson(Map<String, dynamic> json) {
    return DashboardTaskStatsData(
      totalAssigned: json['totalAssigned'] as int? ?? 0,
      pending: json['pending'] as int? ?? 0,
      inProgress: json['inProgress'] as int? ?? 0,
      completed: json['completed'] as int? ?? 0,
    );
  }
}

class DashboardMemberPerformanceItem {
  const DashboardMemberPerformanceItem({
    required this.memberId,
    required this.memberName,
    required this.completedTasks,
    required this.workHours,
    required this.attendanceRate,
    required this.efficiency,
  });

  final int memberId;
  final String memberName;
  final int completedTasks;
  final int workHours;
  final double attendanceRate;
  final int efficiency;

  factory DashboardMemberPerformanceItem.fromJson(Map<String, dynamic> json) {
    return DashboardMemberPerformanceItem(
      memberId: json['memberId'] as int? ?? 0,
      memberName: json['memberName'] as String? ?? '',
      completedTasks: json['completedTasks'] as int? ?? 0,
      workHours: json['workHours'] as int? ?? 0,
      attendanceRate: (json['attendanceRate'] as num?)?.toDouble() ?? 0,
      efficiency: json['efficiency'] as int? ?? 0,
    );
  }
}

class DashboardAlertItem {
  const DashboardAlertItem({
    required this.id,
    required this.type,
    required this.level,
    required this.title,
    required this.message,
    required this.timestamp,
    required this.resolved,
  });

  final int id;
  final String type;
  final String level;
  final String title;
  final String message;
  final String timestamp;
  final bool resolved;

  factory DashboardAlertItem.fromJson(Map<String, dynamic> json) {
    return DashboardAlertItem(
      id: json['id'] as int? ?? 0,
      type: json['type'] as String? ?? '',
      level: json['level'] as String? ?? '',
      title: json['title'] as String? ?? '',
      message: json['message'] as String? ?? '',
      timestamp: json['timestamp'] as String? ?? '',
      resolved: json['resolved'] as bool? ?? false,
    );
  }
}

class DashboardScreenData {
  const DashboardScreenData({
    required this.overview,
    required this.myTasks,
    required this.taskStats,
    required this.memberPerformance,
    required this.alerts,
  });

  final DashboardOverviewResponse overview;
  final List<DashboardTaskSummaryItem> myTasks;
  final DashboardTaskStatsData taskStats;
  final List<DashboardMemberPerformanceItem> memberPerformance;
  final List<DashboardAlertItem> alerts;
}
