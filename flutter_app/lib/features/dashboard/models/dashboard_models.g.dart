// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dashboard_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TrendData _$TrendDataFromJson(Map<String, dynamic> json) => TrendData(
      value: (json['value'] as num).toDouble(),
      direction: json['direction'] as String,
    );

Map<String, dynamic> _$TrendDataToJson(TrendData instance) => <String, dynamic>{
      'value': instance.value,
      'direction': instance.direction,
    };

MetricsData _$MetricsDataFromJson(Map<String, dynamic> json) => MetricsData(
      totalTasks: (json['totalTasks'] as num).toInt(),
      inProgress: (json['inProgress'] as num).toInt(),
      pending: (json['pending'] as num).toInt(),
      completedThisMonth: (json['completedThisMonth'] as num).toInt(),
      systemStatus: json['systemStatus'] as String,
    );

Map<String, dynamic> _$MetricsDataToJson(MetricsData instance) =>
    <String, dynamic>{
      'totalTasks': instance.totalTasks,
      'inProgress': instance.inProgress,
      'pending': instance.pending,
      'completedThisMonth': instance.completedThisMonth,
      'systemStatus': instance.systemStatus,
    };

TrendsData _$TrendsDataFromJson(Map<String, dynamic> json) => TrendsData(
      totalTasksTrend:
          TrendData.fromJson(json['totalTasksTrend'] as Map<String, dynamic>),
      inProgressTrend:
          TrendData.fromJson(json['inProgressTrend'] as Map<String, dynamic>),
      pendingTrend:
          TrendData.fromJson(json['pendingTrend'] as Map<String, dynamic>),
      completedTrend:
          TrendData.fromJson(json['completedTrend'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$TrendsDataToJson(TrendsData instance) =>
    <String, dynamic>{
      'totalTasksTrend': instance.totalTasksTrend,
      'inProgressTrend': instance.inProgressTrend,
      'pendingTrend': instance.pendingTrend,
      'completedTrend': instance.completedTrend,
    };

SystemInfo _$SystemInfoFromJson(Map<String, dynamic> json) => SystemInfo(
      onlineUsers: (json['onlineUsers'] as num).toInt(),
      lastDataSync: json['lastDataSync'] as String,
      systemUptime: json['systemUptime'] as String,
    );

Map<String, dynamic> _$SystemInfoToJson(SystemInfo instance) =>
    <String, dynamic>{
      'onlineUsers': instance.onlineUsers,
      'lastDataSync': instance.lastDataSync,
      'systemUptime': instance.systemUptime,
    };

DashboardOverviewResponse _$DashboardOverviewResponseFromJson(
        Map<String, dynamic> json) =>
    DashboardOverviewResponse(
      metrics: MetricsData.fromJson(json['metrics'] as Map<String, dynamic>),
      trends: TrendsData.fromJson(json['trends'] as Map<String, dynamic>),
      systemInfo:
          SystemInfo.fromJson(json['systemInfo'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$DashboardOverviewResponseToJson(
        DashboardOverviewResponse instance) =>
    <String, dynamic>{
      'metrics': instance.metrics,
      'trends': instance.trends,
      'systemInfo': instance.systemInfo,
    };
