import 'package:json_annotation/json_annotation.dart';

part 'report_models.g.dart';

@JsonSerializable()
class TaskStatistics {
  final int total;
  final int completed;
  @JsonKey(name: 'in_progress')
  final int inProgress;
  final int pending;
  @JsonKey(name: 'completion_rate')
  final double completionRate;
  @JsonKey(name: 'total_work_hours')
  final double totalWorkHours;
  @JsonKey(name: 'avg_work_hours')
  final double avgWorkHours;
  @JsonKey(name: 'online_tasks')
  final int onlineTasks;
  @JsonKey(name: 'offline_tasks')
  final int offlineTasks;

  TaskStatistics({
    required this.total,
    required this.completed,
    required this.inProgress,
    required this.pending,
    required this.completionRate,
    required this.totalWorkHours,
    required this.avgWorkHours,
    required this.onlineTasks,
    required this.offlineTasks,
  });

  factory TaskStatistics.fromJson(Map<String, dynamic> json) => _$TaskStatisticsFromJson(json);
  Map<String, dynamic> toJson() => _$TaskStatisticsToJson(this);
}

@JsonSerializable()
class MemberStatistics {
  final int total;
  final int active;
  @JsonKey(name: 'admin_count')
  final int adminCount;
  @JsonKey(name: 'leader_count')
  final int leaderCount;
  @JsonKey(name: 'member_count')
  final int memberCount;

  MemberStatistics({
    required this.total,
    required this.active,
    required this.adminCount,
    required this.leaderCount,
    required this.memberCount,
  });

  factory MemberStatistics.fromJson(Map<String, dynamic> json) => _$MemberStatisticsFromJson(json);
  Map<String, dynamic> toJson() => _$MemberStatisticsToJson(this);
}

@JsonSerializable()
class AttendanceStatistics {
  @JsonKey(name: 'total_records')
  final int totalRecords;
  @JsonKey(name: 'late_checkins')
  final int lateCheckins;
  @JsonKey(name: 'early_checkouts')
  final int earlyCheckouts;
  @JsonKey(name: 'avg_work_hours')
  final double avgWorkHours;
  @JsonKey(name: 'total_work_hours')
  final double totalWorkHours;
  @JsonKey(name: 'late_rate')
  final double lateRate;

  AttendanceStatistics({
    required this.totalRecords,
    required this.lateCheckins,
    required this.earlyCheckouts,
    required this.avgWorkHours,
    required this.totalWorkHours,
    required this.lateRate,
  });

  factory AttendanceStatistics.fromJson(Map<String, dynamic> json) => _$AttendanceStatisticsFromJson(json);
  Map<String, dynamic> toJson() => _$AttendanceStatisticsToJson(this);
}

@JsonSerializable()
class PeriodData {
  final String from;
  final String to;

  PeriodData({required this.from, required this.to});

  factory PeriodData.fromJson(Map<String, dynamic> json) => _$PeriodDataFromJson(json);
  Map<String, dynamic> toJson() => _$PeriodDataToJson(this);
}

@JsonSerializable()
class StatisticsOverview {
  final PeriodData period;
  final TaskStatistics tasks;
  final MemberStatistics members;
  final AttendanceStatistics attendance;

  StatisticsOverview({
    required this.period,
    required this.tasks,
    required this.members,
    required this.attendance,
  });

  factory StatisticsOverview.fromJson(Map<String, dynamic> json) => _$StatisticsOverviewFromJson(json);
  Map<String, dynamic> toJson() => _$StatisticsOverviewToJson(this);
}
