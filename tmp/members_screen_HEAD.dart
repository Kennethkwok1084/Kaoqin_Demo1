import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/app_strings.dart';
import '../../shared/models/paginated_data.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/app_metric_card.dart';
import '../../shared/widgets/desktop_page.dart';
import '../../shared/widgets/glass_panel.dart';
import '../auth/providers/auth_provider.dart';
import 'models/member_models.dart';
import 'providers/members_provider.dart';

class MembersScreen extends ConsumerStatefulWidget {
  const MembersScreen({super.key});

  @override
  ConsumerState<MembersScreen> createState() => _MembersScreenState();
}

class _MembersScreenState extends ConsumerState<MembersScreen> {
  late final TextEditingController _searchController;
  late final TextEditingController _departmentController;
  late final TextEditingController _classController;
  String? _selectedRole;
  bool? _selectedActive;
  int? _busyMemberId;

  @override
  void initState() {
    super.initState();
    final params = ref.read(membersParamsProvider);
    _searchController = TextEditingController(text: params.search ?? '');
    _departmentController = TextEditingController(text: params.department ?? '');
    _classController = TextEditingController(text: params.className ?? '');
    _selectedRole = params.role;
    _selectedActive = params.isActive;
  }

  @override
  void dispose() {
    _searchController.dispose();
    _departmentController.dispose();
    _classController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final params = ref.watch(membersParamsProvider);
    final membersAsync = ref.watch(membersListProvider);
    final stats = ref.watch(memberStatsProvider).asData?.value;
    final currentUserId = _asInt(ref.watch(authStateProvider).asData?.value?['id']);

    return DesktopPage(
      title: s.membersTitle,
      subtitle: s.membersSubtitle,
      actions: [
        OutlinedButton.icon(
          onPressed: _refresh,
          icon: const Icon(Icons.refresh_rounded),
          label: Text(s.refresh),
        ),
        const SizedBox(width: 12),
        FilledButton.icon(
          onPressed: _createMember,
          icon: const Icon(Icons.person_add_alt_1_rounded),
          label: Text(_t(s, '新增成员', 'New member')),
        ),
      ],
      children: [
        GlassPanel(
          child: Wrap(
            spacing: 12,
            runSpacing: 12,
            crossAxisAlignment: WrapCrossAlignment.end,
            children: [
              SizedBox(
                width: 280,
                child: TextField(
                  controller: _searchController,
                  onSubmitted: (_) => _applyFilters(),
                  decoration: InputDecoration(
                    labelText: _t(s, '搜索', 'Search'),
                    hintText: _t(s, '姓名、学号、用户名', 'Name, student ID, username'),
                    prefixIcon: const Icon(Icons.search_rounded),
                  ),
                ),
              ),
              SizedBox(
                width: 180,
                child: DropdownButtonFormField<String?>(
                  initialValue: _selectedRole,
                  decoration: InputDecoration(labelText: s.role),
                  items: _roleFilterItems(s),
                  onChanged: (value) => setState(() => _selectedRole = value),
                ),
              ),
              SizedBox(
                width: 180,
                child: DropdownButtonFormField<bool?>(
                  initialValue: _selectedActive,
                  decoration: InputDecoration(labelText: s.status),
                  items: [
                    DropdownMenuItem<bool?>(value: null, child: Text(_t(s, '全部状态', 'All statuses'))),
                    DropdownMenuItem<bool?>(value: true, child: Text(_t(s, '启用中', 'Active'))),
                    DropdownMenuItem<bool?>(value: false, child: Text(_t(s, '已停用', 'Inactive'))),
                  ],
                  onChanged: (value) => setState(() => _selectedActive = value),
                ),
              ),
              SizedBox(
                width: 220,
                child: TextField(
                  controller: _departmentController,
                  onSubmitted: (_) => _applyFilters(),
                  decoration: InputDecoration(
                    labelText: s.department,
                    hintText: _t(s, '按部门筛选', 'Filter by department'),
                  ),
                ),
              ),
              SizedBox(
                width: 220,
                child: TextField(
                  controller: _classController,
                  onSubmitted: (_) => _applyFilters(),
                  decoration: InputDecoration(
                    labelText: s.classLabel,
                    hintText: _t(s, '按班级筛选', 'Filter by class'),
                  ),
                ),
              ),
              OutlinedButton.icon(
                onPressed: _resetFilters,
                icon: const Icon(Icons.filter_alt_off_outlined),
                label: Text(s.resetFilters),
              ),
              FilledButton.icon(
                onPressed: _applyFilters,
                icon: const Icon(Icons.filter_alt_rounded),
                label: Text(_t(s, '应用筛选', 'Apply filters')),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        membersAsync.when(
          data: (data) => _MembersBody(
            data: data,
            stats: stats,
            currentPage: params.page,
            busyMemberId: _busyMemberId,
            currentUserId: currentUserId,
            onPageChanged: (page) => ref.read(membersParamsProvider.notifier).setPage(page),
            onEdit: _editMember,
            onPassword: _changePassword,
            onToggleActive: _toggleActive,
            onDelete: _deleteMember,
          ),
          loading: () => DesktopStatusView(
            icon: Icons.people_outline_rounded,
            title: s.loadingMembers,
            message: s.loadingMembersMsg,
          ),
          error: (error, stack) => DesktopStatusView(
            icon: Icons.error_outline_rounded,
            title: s.membersUnavailable,
            message: _readableError(error, s),
            action: FilledButton(onPressed: _refresh, child: Text(s.retry)),
          ),
        ),
      ],
    );
  }

  void _applyFilters() {
    ref.read(membersParamsProvider.notifier).applyFilters(
          search: _searchController.text,
          role: _selectedRole,
          isActive: _selectedActive,
          department: _departmentController.text,
          className: _classController.text,
        );
  }

  void _resetFilters() {
    _searchController.clear();
    _departmentController.clear();
    _classController.clear();
    setState(() {
      _selectedRole = null;
      _selectedActive = null;
    });
    ref.read(membersParamsProvider.notifier).resetFilters();
  }

  void _refresh() {
    ref.invalidate(membersListProvider);
    ref.invalidate(memberStatsProvider);
  }

  Future<void> _createMember() async {
    final payload = await showDialog<Map<String, dynamic>>(
      context: context,
      useRootNavigator: true,
      builder: (_) => const _MemberFormDialog(),
    );
    if (!mounted || payload == null) return;
    await _runCommand(
      successMessage: _t(context.strings, '成员创建成功', 'Member created'),
      command: (service) => service.createMember(payload),
    );
  }

  Future<void> _editMember(MemberItem member) async {
    final payload = await showDialog<Map<String, dynamic>>(
      context: context,
      useRootNavigator: true,
      builder: (_) => _MemberFormDialog(member: member),
    );
    if (!mounted || payload == null) return;
    await _runCommand(
      memberId: member.id,
      successMessage: _t(context.strings, '成员信息已更新', 'Member updated'),
      command: (service) => service.updateMember(member.id, payload),
    );
  }

  Future<void> _changePassword(MemberItem member) async {
    final currentUserId = _asInt(ref.read(authStateProvider).asData?.value?['id']);
    final payload = await showDialog<_PasswordValue>(
      context: context,
      useRootNavigator: true,
      builder: (_) => _PasswordDialog(requireOldPassword: currentUserId == member.id),
    );
    if (!mounted || payload == null) return;
    await _runCommand(
      memberId: member.id,
      successMessage: _t(context.strings, '密码已更新', 'Password updated'),
      command: (service) => service.changePassword(
        memberId: member.id,
        oldPassword: payload.oldPassword,
        newPassword: payload.newPassword,
      ),
    );
  }

  Future<void> _toggleActive(MemberItem member) async {
    final nextActive = !(member.isActive ?? false);
    await _runCommand(
      memberId: member.id,
      successMessage: nextActive
          ? _t(context.strings, '成员已启用', 'Member enabled')
          : _t(context.strings, '成员已停用', 'Member disabled'),
      command: (service) => service.updateMember(member.id, {'is_active': nextActive}),
    );
  }

  Future<void> _deleteMember(MemberItem member) async {
    final s = context.strings;
    final confirmed = await showDialog<bool>(
      context: context,
      useRootNavigator: true,
      builder: (dialogContext) => AlertDialog(
        title: Text(_t(s, '删除成员', 'Delete member')),
        content: Text(
          _t(
            s,
            '确认删除 ${_memberName(member)} 吗？该操作会调用真实删除接口。',
            'Delete ${_memberName(member)}? This will call the real delete API.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text(_t(s, '取消', 'Cancel')),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(_t(s, '删除', 'Delete')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    await _runCommand(
      memberId: member.id,
      successMessage: _t(s, '成员已删除', 'Member deleted'),
      command: (service) => service.deleteMember(member.id),
    );
  }

  Future<void> _runCommand({
    int? memberId,
    required String successMessage,
    required Future<dynamic> Function(MembersCommandService service) command,
  }) async {
    final service = ref.read(membersCommandProvider);
    if (memberId != null) {
      setState(() => _busyMemberId = memberId);
    }
    try {
      await command(service);
      _refresh();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(successMessage)));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_readableError(error, context.strings)),
            backgroundColor: AppColors.danger,
          ),
        );
      }
    } finally {
      if (mounted && memberId != null) {
        setState(() => _busyMemberId = null);
      }
    }
  }
}

class _MembersBody extends StatelessWidget {
  const _MembersBody({
    required this.data,
    required this.stats,
    required this.currentPage,
    required this.busyMemberId,
    required this.currentUserId,
    required this.onPageChanged,
    required this.onEdit,
    required this.onPassword,
    required this.onToggleActive,
    required this.onDelete,
  });

  final PaginatedData<MemberItem> data;
  final MemberStats? stats;
  final int currentPage;
  final int? busyMemberId;
  final int? currentUserId;
  final ValueChanged<int> onPageChanged;
  final ValueChanged<MemberItem> onEdit;
  final ValueChanged<MemberItem> onPassword;
  final ValueChanged<MemberItem> onToggleActive;
  final ValueChanged<MemberItem> onDelete;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    if (data.items.isEmpty) {
      return DesktopStatusView(
        icon: Icons.person_off_outlined,
        title: s.noMembers,
        message: s.noMembersMsg,
      );
    }

    final visibleActiveCount = data.items.where((m) => m.isActive == true).length;
    final departmentCount = data.items
        .map((m) => m.department)
        .whereType<String>()
        .where((v) => v.trim().isNotEmpty)
        .toSet()
        .length;

    return Column(
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            final columns = constraints.maxWidth >= 1180 ? 4 : constraints.maxWidth >= 720 ? 2 : 1;
            return GridView.count(
              crossAxisCount: columns,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              childAspectRatio: 1.45,
              children: [
                AppMetricCard(title: s.visibleMembers, value: '${data.items.length}', icon: Icons.people_alt_outlined, tint: AppColors.accent, caption: s.totalCount(stats?.totalMembers ?? data.total)),
                AppMetricCard(title: s.active, value: '${stats?.activeMembers ?? visibleActiveCount}', icon: Icons.verified_user_outlined, tint: AppColors.success, caption: stats != null ? _t(s, '来自后端统计', 'From backend stats') : _t(s, '当前页启用成员', 'Active on this page')),
                AppMetricCard(title: s.departments, value: '$departmentCount', icon: Icons.domain_rounded, tint: AppColors.warning, caption: _t(s, '当前页可见部门', 'Visible departments')),
                AppMetricCard(title: s.currentPage, value: '${data.page}', icon: Icons.view_day_outlined, tint: AppColors.textSecondary, caption: stats != null ? _t(s, '停用 ${stats!.inactiveMembers} 人', '${stats!.inactiveMembers} inactive') : s.pages(data.totalPages ?? 1)),
              ],
            );
          },
        ),
        const SizedBox(height: 24),
        LayoutBuilder(
          builder: (context, constraints) {
            final columns = constraints.maxWidth >= 1320 ? 3 : constraints.maxWidth >= 860 ? 2 : 1;
            return GridView.builder(
              itemCount: data.items.length,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: columns,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                childAspectRatio: constraints.maxWidth >= 1320 ? 1.4 : 1.25,
              ),
              itemBuilder: (context, index) {
                final member = data.items[index];
                return _MemberCard(
                  member: member,
                  isCurrentUser: currentUserId == member.id,
                  busy: busyMemberId == member.id,
                  onEdit: () => onEdit(member),
                  onPassword: () => onPassword(member),
                  onToggleActive: () => onToggleActive(member),
                  onDelete: () => onDelete(member),
                );
              },
            );
          },
        ),
        const SizedBox(height: 20),
        Row(
          children: [
            Text(_t(s, '共 ${data.total} 名成员', '${data.total} members'), style: Theme.of(context).textTheme.bodySmall),
            const Spacer(),
            OutlinedButton(onPressed: currentPage > 1 ? () => onPageChanged(currentPage - 1) : null, child: Text(s.previousPage)),
            const SizedBox(width: 8),
            ..._pageWindow(currentPage, data.totalPages ?? 1).map(
              (page) => Padding(
                padding: const EdgeInsets.only(right: 8),
                child: page == currentPage
                    ? FilledButton(onPressed: () => onPageChanged(page), child: Text('$page'))
                    : OutlinedButton(onPressed: () => onPageChanged(page), child: Text('$page')),
              ),
            ),
            OutlinedButton(
              onPressed: currentPage < (data.totalPages ?? 1) ? () => onPageChanged(currentPage + 1) : null,
              child: Text(s.nextPage),
            ),
          ],
        ),
      ],
    );
  }
}

class _MemberCard extends StatelessWidget {
  const _MemberCard({
    required this.member,
    required this.isCurrentUser,
    required this.busy,
    required this.onEdit,
    required this.onPassword,
    required this.onToggleActive,
    required this.onDelete,
  });

  final MemberItem member;
  final bool isCurrentUser;
  final bool busy;
  final VoidCallback onEdit;
  final VoidCallback onPassword;
  final VoidCallback onToggleActive;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final isActive = member.isActive == true;
    final displayName = _memberName(member);
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: isActive ? const [AppColors.accent, Color(0xFF635BFF)] : const [Color(0xFF94A3B8), Color(0xFFCBD5E1)]),
                  borderRadius: BorderRadius.circular(16),
                ),
                alignment: Alignment.center,
                child: Text(displayName.substring(0, 1).toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
              ),
              const Spacer(),
              _StatusChip(label: member.statusDisplay ?? (isActive ? s.active : s.inactive), color: isActive ? AppColors.success : AppColors.textSecondary),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(child: Text(displayName, maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.titleMedium)),
              if (isCurrentUser) _StatusChip(label: _t(s, '当前账号', 'Current user'), color: AppColors.accent),
            ],
          ),
          const SizedBox(height: 6),
          Text(member.studentId ?? member.username, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 18),
          _InfoRow(label: s.role, value: _roleLabel(s, member.role)),
          _InfoRow(label: s.department, value: member.department ?? s.unassignedDepartment),
          _InfoRow(label: s.classLabel, value: member.className ?? s.na),
          _InfoRow(label: s.phone, value: member.phone ?? s.na),
          _InfoRow(label: _t(s, '加入日期', 'Join date'), value: _formatDate(member.joinDate)),
          const Spacer(),
          if (busy)
            const Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)))
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _ActionChip(icon: Icons.edit_outlined, label: _t(s, '编辑', 'Edit'), onTap: onEdit),
                _ActionChip(icon: Icons.lock_outline_rounded, label: _t(s, '改密', 'Password'), onTap: onPassword),
                _ActionChip(icon: isActive ? Icons.pause_circle_outline_rounded : Icons.play_circle_outline_rounded, label: isActive ? _t(s, '停用', 'Disable') : _t(s, '启用', 'Enable'), onTap: onToggleActive),
                _ActionChip(icon: Icons.delete_outline_rounded, label: _t(s, '删除', 'Delete'), onTap: onDelete, danger: true),
              ],
            ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(width: 92, child: Text(label, style: Theme.of(context).textTheme.bodySmall)),
          Expanded(child: Text(value, maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600))),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(999)),
      child: Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: color, fontWeight: FontWeight.w700)),
    );
  }
}

class _ActionChip extends StatelessWidget {
  const _ActionChip({
    required this.icon,
    required this.label,
    required this.onTap,
    this.danger = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    final foreground = danger ? AppColors.danger : AppColors.textPrimary;
    final border = danger ? AppColors.danger.withValues(alpha: 0.2) : AppColors.borderStrong;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: AppColors.surfaceStrong,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: foreground),
            const SizedBox(width: 6),
            Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: foreground, fontWeight: FontWeight.w700)),
          ],
        ),
      ),
    );
  }
}

class _MemberFormDialog extends StatefulWidget {
  const _MemberFormDialog({this.member});

  final MemberItem? member;

  @override
  State<_MemberFormDialog> createState() => _MemberFormDialogState();
}

class _MemberFormDialogState extends State<_MemberFormDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _usernameController;
  late final TextEditingController _nameController;
  late final TextEditingController _studentIdController;
  late final TextEditingController _phoneController;
  late final TextEditingController _departmentController;
  late final TextEditingController _classController;
  late final TextEditingController _passwordController;
  late String _role;
  late bool _isActive;

  bool get _isEdit => widget.member != null;

  @override
  void initState() {
    super.initState();
    final member = widget.member;
    _usernameController = TextEditingController(text: member?.username ?? '');
    _nameController = TextEditingController(text: member?.name ?? '');
    _studentIdController = TextEditingController(text: member?.studentId ?? '');
    _phoneController = TextEditingController(text: member?.phone ?? '');
    _departmentController = TextEditingController(text: member?.department ?? '');
    _classController = TextEditingController(text: member?.className ?? '');
    _passwordController = TextEditingController(text: '123456');
    _role = member?.role ?? 'member';
    _isActive = member?.isActive ?? true;
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _nameController.dispose();
    _studentIdController.dispose();
    _phoneController.dispose();
    _departmentController.dispose();
    _classController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    return AlertDialog(
      title: Text(_isEdit ? _t(s, '编辑成员', 'Edit member') : _t(s, '新增成员', 'New member')),
      content: SizedBox(
        width: 560,
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _twoColumn(
                  TextFormField(
                    controller: _usernameController,
                    decoration: InputDecoration(labelText: _t(s, '用户名', 'Username')),
                    validator: (value) {
                      final input = value?.trim() ?? '';
                      if (input.isEmpty) return _t(s, '请输入用户名', 'Enter a username');
                      if (!RegExp(r'^[A-Za-z0-9_]+$').hasMatch(input)) {
                        return _t(s, '仅支持字母、数字和下划线', 'Letters, numbers, and underscore only');
                      }
                      return null;
                    },
                  ),
                  TextFormField(
                    controller: _nameController,
                    decoration: InputDecoration(labelText: _t(s, '姓名', 'Name')),
                    validator: (value) => (value?.trim().isEmpty ?? true) ? _t(s, '请输入姓名', 'Enter a name') : null,
                  ),
                ),
                const SizedBox(height: 12),
                _twoColumn(
                  TextFormField(
                    controller: _studentIdController,
                    decoration: InputDecoration(labelText: _t(s, '学号', 'Student ID')),
                    validator: (value) {
                      final input = value?.trim() ?? '';
                      if (input.isNotEmpty && !RegExp(r'^[A-Za-z0-9]+$').hasMatch(input)) {
                        return _t(s, '学号仅支持字母和数字', 'Student ID must be alphanumeric');
                      }
                      return null;
                    },
                  ),
                  TextFormField(
                    controller: _phoneController,
                    decoration: InputDecoration(labelText: s.phone),
                    validator: (value) {
                      final input = value?.trim() ?? '';
                      if (input.isNotEmpty && !RegExp(r'^\d{11}$').hasMatch(input)) {
                        return _t(s, '手机号需为 11 位数字', 'Phone must be 11 digits');
                      }
                      return null;
                    },
                  ),
                ),
                const SizedBox(height: 12),
                _twoColumn(
                  TextFormField(
                    controller: _departmentController,
                    decoration: InputDecoration(labelText: s.department),
                    validator: (value) => (value?.trim().isEmpty ?? true) ? _t(s, '请输入部门', 'Enter a department') : null,
                  ),
                  TextFormField(
                    controller: _classController,
                    decoration: InputDecoration(labelText: s.classLabel),
                    validator: (value) => (value?.trim().isEmpty ?? true) ? _t(s, '请输入班级', 'Enter a class') : null,
                  ),
                ),
                const SizedBox(height: 12),
                _twoColumn(
                  DropdownButtonFormField<String>(
                    initialValue: _role,
                    decoration: InputDecoration(labelText: s.role),
                    items: _roleItems(s),
                    onChanged: (value) {
                      if (value != null) setState(() => _role = value);
                    },
                  ),
                  _isEdit
                      ? SwitchListTile(
                          value: _isActive,
                          contentPadding: EdgeInsets.zero,
                          title: Text(_t(s, '启用状态', 'Active status')),
                          onChanged: (value) => setState(() => _isActive = value),
                        )
                      : TextFormField(
                          controller: _passwordController,
                          obscureText: true,
                          decoration: InputDecoration(labelText: _t(s, '初始密码', 'Initial password')),
                          validator: (value) => (value?.trim().length ?? 0) < 6 ? _t(s, '密码至少 6 位', 'Password must be at least 6 characters') : null,
                        ),
                ),
                if (!_isEdit)
                  SwitchListTile(
                    value: _isActive,
                    contentPadding: EdgeInsets.zero,
                    title: Text(_t(s, '启用状态', 'Active status')),
                    onChanged: (value) => setState(() => _isActive = value),
                  ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(_t(s, '取消', 'Cancel'))),
        FilledButton(onPressed: _submit, child: Text(_isEdit ? _t(s, '保存', 'Save') : _t(s, '创建', 'Create'))),
      ],
    );
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    final payload = <String, dynamic>{
      'username': _usernameController.text.trim(),
      'name': _nameController.text.trim(),
      'student_id': _normalizeText(_studentIdController.text),
      'phone': _normalizeText(_phoneController.text),
      'department': _departmentController.text.trim(),
      'class_name': _classController.text.trim(),
      'role': _role,
      'is_active': _isActive,
    };
    if (!_isEdit) {
      payload['password'] = _passwordController.text.trim();
      payload['profile_completed'] = false;
    }
    Navigator.of(context).pop(payload);
  }
}

class _PasswordDialog extends StatefulWidget {
  const _PasswordDialog({required this.requireOldPassword});

  final bool requireOldPassword;

  @override
  State<_PasswordDialog> createState() => _PasswordDialogState();
}

class _PasswordDialogState extends State<_PasswordDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _oldPasswordController;
  late final TextEditingController _newPasswordController;

  @override
  void initState() {
    super.initState();
    _oldPasswordController = TextEditingController();
    _newPasswordController = TextEditingController();
  }

  @override
  void dispose() {
    _oldPasswordController.dispose();
    _newPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    return AlertDialog(
      title: Text(_t(s, '修改密码', 'Change password')),
      content: SizedBox(
        width: 420,
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (widget.requireOldPassword) ...[
                TextFormField(
                  controller: _oldPasswordController,
                  obscureText: true,
                  decoration: InputDecoration(labelText: _t(s, '旧密码', 'Current password')),
                  validator: (value) => (value?.trim().isEmpty ?? true) ? _t(s, '请输入旧密码', 'Enter the current password') : null,
                ),
                const SizedBox(height: 12),
              ],
              TextFormField(
                controller: _newPasswordController,
                obscureText: true,
                decoration: InputDecoration(labelText: _t(s, '新密码', 'New password')),
                validator: (value) => (value?.trim().length ?? 0) < 6 ? _t(s, '密码至少 6 位', 'Password must be at least 6 characters') : null,
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(_t(s, '取消', 'Cancel'))),
        FilledButton(
          onPressed: () {
            if (!_formKey.currentState!.validate()) return;
            Navigator.of(context).pop(
              _PasswordValue(
                oldPassword: _normalizeText(_oldPasswordController.text),
                newPassword: _newPasswordController.text.trim(),
              ),
            );
          },
          child: Text(_t(s, '提交', 'Submit')),
        ),
      ],
    );
  }
}

class _PasswordValue {
  const _PasswordValue({required this.oldPassword, required this.newPassword});

  final String? oldPassword;
  final String newPassword;
}

List<DropdownMenuItem<String?>> _roleFilterItems(AppStrings s) {
  return [
    DropdownMenuItem<String?>(value: null, child: Text(_t(s, '全部角色', 'All roles'))),
    ..._roleItems(s).map((item) => DropdownMenuItem<String?>(value: item.value, child: item.child)),
  ];
}

List<DropdownMenuItem<String>> _roleItems(AppStrings s) {
  return [
    DropdownMenuItem<String>(value: 'admin', child: Text(_t(s, '管理员', 'Admin'))),
    DropdownMenuItem<String>(value: 'group_leader', child: Text(_t(s, '组长', 'Group leader'))),
    DropdownMenuItem<String>(value: 'member', child: Text(_t(s, '成员', 'Member'))),
    DropdownMenuItem<String>(value: 'guest', child: Text(_t(s, '访客', 'Guest'))),
  ];
}

String _roleLabel(AppStrings s, String? role) {
  switch (role) {
    case 'admin':
      return _t(s, '管理员', 'Admin');
    case 'group_leader':
      return _t(s, '组长', 'Group leader');
    case 'guest':
      return _t(s, '访客', 'Guest');
    default:
      return _t(s, '成员', 'Member');
  }
}

String _memberName(MemberItem member) {
  final name = member.name?.trim();
  return (name != null && name.isNotEmpty) ? name : member.username;
}

String _formatDate(String? raw) {
  if (raw == null || raw.trim().isEmpty) return '--';
  try {
    final dt = DateTime.parse(raw).toLocal();
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
  } catch (_) {
    return raw;
  }
}

List<int> _pageWindow(int currentPage, int totalPages) {
  if (totalPages <= 1) return const [1];
  final safeTotal = totalPages < 1 ? 1 : totalPages;
  final start = (currentPage - 1).clamp(1, safeTotal);
  final end = (start + 2).clamp(1, safeTotal);
  final adjustedStart = (end - 2).clamp(1, safeTotal);
  return [for (int page = adjustedStart; page <= end; page++) page];
}

String _readableError(Object error, AppStrings s) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      return data['detail'] as String? ?? data['message'] as String? ?? error.message ?? _t(s, '操作失败', 'Operation failed');
    }
    if (data is Map) {
      final map = Map<String, dynamic>.from(data);
      return map['detail'] as String? ?? map['message'] as String? ?? error.message ?? _t(s, '操作失败', 'Operation failed');
    }
    return error.message ?? _t(s, '操作失败', 'Operation failed');
  }
  final message = error.toString().replaceFirst('Exception: ', '').trim();
  return message.isEmpty ? _t(s, '操作失败', 'Operation failed') : message;
}

String? _normalizeText(String? value) {
  final trimmed = value?.trim();
  return (trimmed == null || trimmed.isEmpty) ? null : trimmed;
}

String _t(AppStrings s, String zh, String en) => s.isZh ? zh : en;

int? _asInt(Object? value) {
  if (value is int) return value;
  if (value is String) return int.tryParse(value);
  return null;
}

Widget _twoColumn(Widget left, Widget right) {
  return Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Expanded(child: left),
      const SizedBox(width: 12),
      Expanded(child: right),
    ],
  );
}
