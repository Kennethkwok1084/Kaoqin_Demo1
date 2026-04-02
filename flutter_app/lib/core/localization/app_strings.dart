import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

import 'app_locale.dart';

class AppStrings {
  AppStrings(this.language);

  final AppLanguage language;

  static const LocalizationsDelegate<AppStrings> delegate = _AppStringsDelegate();

  static AppStrings of(BuildContext context) {
    final strings = Localizations.of<AppStrings>(context, AppStrings);
    assert(strings != null, 'AppStrings not found in context');
    return strings!;
  }

  bool get isZh => language == AppLanguage.zh;

  String _t(String zh, String en) => isZh ? zh : en;

  String get appTitle => _t('学生网管考勤', 'Campus Ops Desktop');
  String get departmentName => _t('信息化建设处', 'Information Office');
  String get dashboardNav => _t('工作台', 'Dashboard');
  String get tasksNav => _t('任务管理', 'Tasks');
  String get workHoursNav => _t('工时记录', 'Work Hours');
  String get membersNav => _t('成员管理', 'Members');
  String get reportsNav => _t('统计报表', 'Reports');
  String get overview => _t('综合概览', 'Overview');
  String get taskQueue => _t('任务与处置', 'Task queue');
  String get hoursAndAttendance => _t('工时与考勤', 'Attendance and hours');
  String get peopleAndSchedule => _t('成员与组织', 'People and schedule');
  String get analytics => _t('统计与分析', 'Analytics');
  String get settings => _t('系统设置', 'Settings');
  String get signOut => _t('退出登录', 'Sign out');
  String get searchHint => _t('搜索工单、姓名、地点', 'Search tickets, names, and locations');
  String get languageChinese => _t('中文', 'Chinese');
  String get languageEnglish => _t('英文', 'English');
  String get loginFailed => _t('登录失败', 'Login failed');
  String get invalidCredentials => _t('账号或密码错误', 'Invalid student ID or password');
  String get accountDisabled =>
      _t('账号已停用，请联系管理员', 'Account disabled. Contact an administrator.');
  String get signIn => _t('登录系统', 'Sign in');
  String get accountHint => _t('学号', 'Student ID');
  String get passwordHint => _t('密码', 'Password');
  String get enterAccountId => _t('请输入账号', 'Enter your account ID');
  String get enterPassword => _t('请输入密码', 'Enter your password');
  String get continueLabel => _t('进入工作台', 'Continue');
  String get loginSubtitle =>
      _t('使用校园统一账号登录桌面管理端。', 'Use your campus account to enter the desktop workspace.');
  String get loginHeroSubtitle => _t(
        'Windows 桌面端采用 macOS / iOS 风格设计语言，统一承载任务管理、工时记录、成员管理与统计分析等核心业务。',
        'The Windows desktop is rebuilt with a macOS and iOS visual language while keeping tasks, hours, members, and reports in one workspace.',
      );
  String get desktopShell => _t('桌面工作台', 'Desktop shell');
  String get taskCenter => _t('任务大厅', 'Task center');
  String get reportsAndHours => _t('报表与工时', 'Reports and hours');

  String get dashboardTitle => _t('工作台', 'Dashboard');
  String get dashboardSubtitle => _t(
        '集中呈现系统关键指标、快捷操作入口、近期任务动态与重要通知信息。',
        'Rebuilt from the 1.html information layout with stats, quick actions, recent tasks, and a right-side info lane.',
      );
  String get refresh => _t('刷新', 'Refresh');
  String get retry => _t('重试', 'Retry');
  String get createTask => _t('新建任务', 'New task');
  String get filter => _t('筛选', 'Filter');
  String get applySearch => _t('应用搜索', 'Apply search');
  String get loadingDashboard => _t('正在加载工作台', 'Loading dashboard');
  String get loadingDashboardMsg =>
      _t('正在同步概览指标和系统状态。', 'Syncing overview metrics and system status.');
  String get dashboardUnavailable => _t('工作台不可用', 'Dashboard unavailable');
  String get monthHours => _t('本月累计工时', 'Monthly hours');
  String get pendingTasks => _t('待处理任务', 'Pending tasks');
  String get weeklyWarnings => _t('本周告警', 'Weekly warnings');
  String get monthlyCompleted => _t('本月完成', 'Completed this month');
  String get quickActions => _t('快捷操作', 'Quick actions');
  String get quickActionsSubtitle => _t(
        '提供高频业务的快速入口，便于在工作台中直接发起常用操作。',
        'Three-card action zone inspired by 1.html with one primary and two supporting actions.',
      );
  String get registerAssistTask => _t('登记协助任务', 'Register assist task');
  String get registerAssistTaskDesc => _t(
        '登记跨部门协作任务，并同步形成可追踪的处理记录。',
        'Create manual cross-team support records and sync them into the task flow.',
      );
  String get importOfflineOrder => _t('导入线下单', 'Import offline ticket');
  String get importOfflineOrderDesc => _t(
        '补录线下工单与现场处置记录，确保业务数据完整留痕。',
        'Bring field work and offline tickets back into the system.',
      );
  String get claimPendingOrder => _t('认领待处理单', 'Claim pending ticket');
  String get claimPendingOrderDesc => _t(
        '快速认领待处理任务，缩短任务响应与分派时间。',
        'Jump into the hottest queue and claim work directly.',
      );
  String get recentTasks => _t('近期任务动态', 'Recent tasks');
  String get recentTasksSubtitle => _t(
        '按桌面工作台方式展示近期任务状态、位置、时限与处理进度。',
        'Card-style task table inspired by 1.html.',
      );
  String get rankingTitle => _t('本月工时排行', 'Monthly ranking');
  String get rankingSubtitle => _t('展示成员工作量与完成情况的阶段性排序。', 'Ranking card aligned with the right sidebar in 1.html.');
  String get viewFullRanking => _t('查看完整榜单', 'View full ranking');
  String get systemNotice => _t('系统公告', 'System notice');
  String get viewDetails => _t('了解详情', 'View details');
  String get workbenchTaskInfo => _t('工单信息', 'Task info');
  String get location => _t('地点', 'Location');
  String get status => _t('状态', 'Status');
  String get reward => _t('预计收益', 'Reward');
  String get owner => _t('报修人 / 地点', 'Owner / Location');
  String get systemNoticeMessage => _t(
        '本周将进行系统数据结转，请在周五前补齐线下工单和协助记录，避免影响工时统计。',
        'A system rollover is scheduled this week. Please complete offline tickets and support records before Friday to avoid affecting hour statistics.',
      );
  String get sampleTaskNetworkTitleLegacy => _t(
        '无法连接校园网，提示认证失败',
        'Cannot connect to campus network, authentication failed',
      );
  String get sampleTaskSwitchTitleLegacy => _t(
        '核心交换机端口故障排查',
        'Investigate a core switch port failure',
      );
  String get sampleTaskSupportTitleLegacy => _t(
        '协助迎新现场网络部署',
        'Support onsite network setup for orientation',
      );

  String get tasksTitle => _t('任务管理', 'Tasks');
  String get tasksSubtitle => _t(
        '统一管理任务查询、状态筛选、过程处置与多维信息展示。',
        'Desktop task hall aligned with 1.html, with segmented tabs, filters, search, and a multi-column table.',
      );
  String get resetFilters => _t('重置筛选', 'Reset filters');
  String get applySearchHint => _t('搜索任务标题、地点或处理人', 'Search title, location, or assignee');
  String get loadingTasks => _t('正在加载任务列表', 'Loading tasks');
  String get loadingTasksMsg => _t('正在同步最新任务队列。', 'Syncing the latest task queue.');
  String get tasksUnavailable => _t('任务列表不可用', 'Tasks unavailable');
  String get noTasks => _t('暂无任务数据', 'No tasks found');
  String get noTasksMsg => _t('当前筛选条件下没有可展示的任务。', 'No tasks match the current filter.');
  String get taskContent => _t('任务内容', 'Task content');
  String get ownerAndLocation => _t('负责人 / 地点', 'Owner / Location');
  String get timeline => _t('时间限制', 'Timeline');
  String get statusPriority => _t('状态 / 优先级', 'Status / Priority');
  String get noDescription => _t('暂无任务说明', 'No description');
  String get unassigned => _t('待分配', 'Unassigned');
  String get noLocation => _t('未填写地点', 'No location');
  String get all => _t('全部', 'All');
  String get processing => _t('处理中', 'In progress');
  String get completed => _t('已完成', 'Completed');
  String get pending => _t('待处理', 'Pending');
  String get regular => _t('常规', 'Normal');
  String get urgent => _t('紧急', 'Urgent');
  String get high => _t('高优先级', 'High');
  String get medium => _t('中优先级', 'Medium');
  String get low => _t('低优先级', 'Low');
  String get cancelled => _t('已取消', 'Cancelled');
  String get unknown => _t('未知', 'Unknown');
  String get created => _t('创建', 'Created');
  String get due => _t('截止', 'Due');
  String get notSet => _t('未设置', 'Not set');
  String get repairTag => _t('报修', 'Repair');
  String get fieldTag => _t('现场', 'Field');
  String get supportTag => _t('协助', 'Support');
  String get onlineTag => _t('线上单', 'Online');
  String get genericTaskTag => _t('任务', 'Task');
  String get dueSoon => _t('即将超时', 'Due soon');
  String get arrived => _t('已到期', 'Expired');
  String get previousPage => _t('上一页', 'Previous');
  String get nextPage => _t('下一页', 'Next');
  String deadlineLabel(String value) => _t('截止 $value', 'Due $value');
  String createdAtLabel(String value) => _t('创建于 $value', 'Created $value');

  String get workHoursTitle => _t('工时记录', 'Work Hours');
  String get workHoursSubtitle => _t(
        '集中展示工时记录、补录数据与时间维度统计结果。',
        'Desktop presentation of recorded effort, manual entries, and time slices.',
      );
  String get loadingWorkHours => _t('正在加载工时记录', 'Loading work hours');
  String get loadingWorkHoursMsg =>
      _t('正在整理桌面时间线所需的记录。', 'Collecting records for the desktop timeline.');
  String get workHoursUnavailable => _t('工时记录不可用', 'Work hours unavailable');
  String get noWorkHours => _t('暂无工时记录', 'No work-hour records');
  String get noWorkHoursMsg =>
      _t('当前筛选范围内还没有同步数据。', 'The selected range does not contain any synced data yet.');
  String get loggedHours => _t('已登记工时', 'Logged hours');
  String get manualRecords => _t('手动记录', 'Manual records');
  String get handAdded => _t('人工补录', 'Hand-added');
  String get ratedTasks => _t('已评分任务', 'Rated tasks');
  String get qualitySignal => _t('质量信号', 'Quality signal');
  String get membersInvolved => _t('参与成员', 'Members involved');
  String get uniqueContributors => _t('去重参与人', 'Unique contributors');
  String get entry => _t('条目', 'Entry');
  String get member => _t('成员', 'Member');
  String get date => _t('日期', 'Date');
  String get type => _t('类型', 'Type');
  String get hours => _t('工时', 'Hours');
  String get unknownMember => _t('未知成员', 'Unknown');
  String get noDate => _t('无日期', 'No date');
  String get general => _t('通用', 'General');
  String totalRecords(int total) => _t('共 $total 条记录', '$total records');
  String totalCount(int total) => _t('共 $total 条', '$total total');
  String pages(int pages) => _t('$pages 页', '$pages pages');
  String workHourEntries(int count) => _t('$count 条记录', '$count entries');
  String workHourRecordLabel(int id) => _t('工时记录 #$id', 'Work-hour record #$id');
  String remainingHours(int hours) => _t('剩余 $hours 小时', '$hours hours left');
  String remainingDays(int days) => _t('剩余 $days 天', '$days days left');

  String get membersTitle => _t('成员管理', 'Members');
  String get membersSubtitle => _t(
        '集中维护成员信息、启停状态、账号密码与组织属性。',
        'Directory and roster view rebuilt into a desktop panel layout.',
      );
  String get loadingMembers => _t('正在加载成员目录', 'Loading member directory');
  String get loadingMembersMsg =>
      _t('正在整理桌面 roster 和状态芯片。', 'Preparing the desktop roster and status chips.');
  String get membersUnavailable => _t('成员列表不可用', 'Members unavailable');
  String get noMembers => _t('没有成员数据', 'No members found');
  String get noMembersMsg => _t('当前查询没有返回任何成员。', 'The current directory query returned zero rows.');
  String get visibleMembers => _t('可见成员', 'Visible members');
  String get active => _t('启用中', 'Active');
  String get currentlyEnabled => _t('当前启用', 'Currently enabled');
  String get departments => _t('部门数', 'Departments');
  String get visibleGroups => _t('可见分组', 'Visible groups');
  String get currentPage => _t('当前页', 'Current page');
  String get role => _t('角色', 'Role');
  String get memberRole => _t('成员', 'Member');
  String get department => _t('部门', 'Department');
  String get unassignedDepartment => _t('未分配', 'Unassigned');
  String get classLabel => _t('班级', 'Class');
  String get phone => _t('电话', 'Phone');
  String get inactive => _t('未启用', 'Inactive');
  String get na => _t('无', 'N/A');

  String get reportsTitle => _t('统计报表', 'Reports');
  String get reportsSubtitle => _t(
        '汇总展示考勤、任务与成员相关的关键统计指标和趋势信息。',
        'Summary cards for attendance, tasks, and membership trends.',
      );
  String get loadingReports => _t('正在加载报表', 'Loading reports');
  String get loadingReportsMsg =>
      _t('正在汇总桌面概览所需的统计信息。', 'Collecting aggregated statistics for the desktop overview.');
  String get reportsUnavailable => _t('报表不可用', 'Reports unavailable');
  String get attendance => _t('考勤', 'Attendance');
  String get hoursLateRateRecords => _t('工时、迟到率与打卡记录。', 'Hours, late rate, and total check-in records.');
  String get totalHours => _t('总工时', 'Total hours');
  String get averageHours => _t('平均工时', 'Average hours');
  String get lateRate => _t('迟到率', 'Late rate');
  String get records => _t('记录数', 'Records');
  String get tasksSection => _t('任务', 'Tasks');
  String get completionAndQueue => _t('完成度与队列构成。', 'Completion and queue composition.');
  String get totalTasks => _t('任务总数', 'Total tasks');
  String get completionRate => _t('完成率', 'Completion rate');
  String get inProgress => _t('处理中', 'In progress');
  String get membersSection => _t('成员', 'Members');
  String get headcountAndRoster => _t('人数与活跃 roster。', 'Headcount and active roster.');
  String get totalMembers => _t('成员总数', 'Total members');
  String get leads => _t('负责人', 'Leads');
  String get admins => _t('管理员', 'Admins');
  String get insightLane => _t('洞察栏', 'Insight lane');
  String get insightLaneSubtitle =>
      _t('为桌面端保留紧凑的上下文和复核卡片。', 'Compact cards for desktop context and review.');
  String get reportingPeriod => _t('统计周期', 'Reporting period');
  String get from => _t('开始', 'From');
  String get to => _t('结束', 'To');
  String get lateCheckins => _t('迟到签到', 'Late check-ins');
  String get earlyCheckouts => _t('早退签退', 'Early checkouts');
  String get desktopNote => _t('桌面说明', 'Desktop note');
  String get desktopNoteText => _t(
        '当前页面以关键指标快速浏览为主，后续可在不调整整体结构的前提下继续扩展筛选与明细能力。',
        'This screen now prioritizes fast scanning over deep drill-down. Detailed filters can be layered later without changing the card grid.',
      );

  String get sampleTaskNetworkTitle => _t(
        '无法连接校园网，提示认证失败',
        'Cannot connect to campus network, authentication failed',
      );
  String get sampleTaskSwitchTitle =>
      _t('核心交换机端口故障排查', 'Investigate a core switch port failure');
  String get sampleTaskSupportTitle =>
      _t('协助迎新现场网络部署', 'Support onsite network setup for orientation');

  String rankMe(String name) => _t('$name（我）', '$name (Me)');
}

class _AppStringsDelegate extends LocalizationsDelegate<AppStrings> {
  const _AppStringsDelegate();

  @override
  bool isSupported(Locale locale) => ['zh', 'en'].contains(locale.languageCode);

  @override
  Future<AppStrings> load(Locale locale) {
    return SynchronousFuture(
      AppStrings(locale.languageCode == 'en' ? AppLanguage.en : AppLanguage.zh),
    );
  }

  @override
  bool shouldReload(covariant LocalizationsDelegate<AppStrings> old) => false;
}

extension AppStringsContextX on BuildContext {
  AppStrings get strings => AppStrings.of(this);
}
