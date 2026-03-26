// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'report_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TaskStatistics _$TaskStatisticsFromJson(Map<String, dynamic> json) =>
    TaskStatistics(
      total: (json['total'] as num).toInt(),
      completed: (json['completed'] as num).toInt(),
      inProgress: (json['in_progress'] as num).toInt(),
      pending: (json['pending'] as num).toInt(),
      completionRate: (json['completion_rate'] as num).toDouble(),
      totalWorkHours: (json['total_work_hours'] as num).toDouble(),
      avgWorkHours: (json['avg_work_hours'] as num).toDouble(),
      onlineTasks: (json['online_tasks'] as num).toInt(),
      offlineTasks: (json['offline_tasks'] as num).toInt(),
    );

Map<String, dynamic> _$TaskStatisticsToJson(TaskStatistics instance) =>
    <String, dynamic>{
      'total': instance.total,
      'completed': instance.completed,
      'in_progress': instance.inProgress,
      'pending': instance.pending,
      'completion_rate': instance.completionRate,
      'total_work_hours': instance.totalWorkHours,
      'avg_work_hours': instance.avgWorkHours,
      'online_tasks': instance.onlineTasks,
      'offline_tasks': instance.offlineTasks,
    };

MemberStatistics _$MemberStatisticsFromJson(Map<String, dynamic> json) =>
    MemberStatistics(
      total: (json['total'] as num).toInt(),
      active: (json['active'] as num).toInt(),
      adminCount: (json['admin_count'] as num).toInt(),
      leaderCount: (json['leader_count'] as num).toInt(),
      memberCount: (json['member_count'] as num).toInt(),
    );

Map<String, dynamic> _$MemberStatisticsToJson(MemberStatistics instance) =>
    <String, dynamic>{
      'total': instance.total,
      'active': instance.active,
      'admin_count': instance.adminCount,
      'leader_count': instance.leaderCount,
      'member_count': instance.memberCount,
    };

AttendanceStatistics _$AttendanceStatisticsFromJson(
        Map<String, dynamic> json) =>
    AttendanceStatistics(
      totalRecords: (json['total_records'] as num).toInt(),
      lateCheckins: (json['late_checkins'] as num).toInt(),
      earlyCheckouts: (json['early_checkouts'] as num).toInt(),
      avgWorkHours: (json['avg_work_hours'] as num).toDouble(),
      totalWorkHours: (json['total_work_hours'] as num).toDouble(),
      lateRate: (json['late_rate'] as num).toDouble(),
    );

Map<String, dynamic> _$AttendanceStatisticsToJson(
        AttendanceStatistics instance) =>
    <String, dynamic>{
      'total_records': instance.totalRecords,
      'late_checkins': instance.lateCheckins,
      'early_checkouts': instance.earlyCheckouts,
      'avg_work_hours': instance.avgWorkHours,
      'total_work_hours': instance.totalWorkHours,
      'late_rate': instance.lateRate,
    };

PeriodData _$PeriodDataFromJson(Map<String, dynamic> json) => PeriodData(
      from: json['from'] as String,
      to: json['to'] as String,
    );

Map<String, dynamic> _$PeriodDataToJson(PeriodData instance) =>
    <String, dynamic>{
      'from': instance.from,
      'to': instance.to,
    };

StatisticsOverview _$StatisticsOverviewFromJson(Map<String, dynamic> json) =>
    StatisticsOverview(
      period: PeriodData.fromJson(json['period'] as Map<String, dynamic>),
      tasks: TaskStatistics.fromJson(json['tasks'] as Map<String, dynamic>),
      members:
          MemberStatistics.fromJson(json['members'] as Map<String, dynamic>),
      attendance: AttendanceStatistics.fromJson(
          json['attendance'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$StatisticsOverviewToJson(StatisticsOverview instance) =>
    <String, dynamic>{
      'period': instance.period,
      'tasks': instance.tasks,
      'members': instance.members,
      'attendance': instance.attendance,
    };
