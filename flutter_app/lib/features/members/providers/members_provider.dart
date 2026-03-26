import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_provider.dart';
import '../../../shared/models/paginated_data.dart';
import '../api/members_api_client.dart';
import '../models/member_models.dart';

final membersApiClientProvider = Provider<MembersApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return MembersApiClient(dio);
});

class MembersParams {
  final int page;
  final int pageSize;
  final String? search;
  final String? role;

  const MembersParams({
    this.page = 1,
    this.pageSize = 20,
    this.search,
    this.role,
  });
}

class MembersParamsNotifier extends Notifier<MembersParams> {
  @override
  MembersParams build() => const MembersParams();

  void updateParams({int? page, int? pageSize, String? search, String? role}) {
    state = MembersParams(
      page: page ?? state.page,
      pageSize: pageSize ?? state.pageSize,
      search: search ?? state.search,
      role: role ?? state.role,
    );
  }
}

final membersParamsProvider = NotifierProvider<MembersParamsNotifier, MembersParams>(() {
  return MembersParamsNotifier();
});

final membersListProvider = FutureProvider<PaginatedData<MemberItem>>((ref) async {
  final client = ref.watch(membersApiClientProvider);
  final params = ref.watch(membersParamsProvider);
  
  final response = await client.getMembers(
    params.page,
    params.pageSize,
    search: params.search,
    role: params.role,
  );

  if (response.success && response.data != null) {
    return response.data!;
  } else {
    throw Exception(response.message);
  }
});
