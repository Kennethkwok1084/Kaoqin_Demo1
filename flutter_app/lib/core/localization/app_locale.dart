import 'dart:ui';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../utils/prefs_provider.dart';

enum AppLanguage {
  zh,
  en,
}

extension AppLanguageX on AppLanguage {
  Locale get locale => switch (this) {
        AppLanguage.zh => const Locale('zh'),
        AppLanguage.en => const Locale('en'),
      };

  String get code => switch (this) {
        AppLanguage.zh => 'zh',
        AppLanguage.en => 'en',
      };

  static AppLanguage fromCode(String? code) {
    return code == 'en' ? AppLanguage.en : AppLanguage.zh;
  }
}

class AppLanguageNotifier extends Notifier<AppLanguage> {
  static const _prefsKey = 'app_language';

  @override
  AppLanguage build() {
    final prefs = ref.watch(prefsProvider);
    return AppLanguageX.fromCode(prefs.getString(_prefsKey));
  }

  Future<void> setLanguage(AppLanguage language) async {
    state = language;
    final prefs = ref.read(prefsProvider);
    await prefs.setString(_prefsKey, language.code);
  }

  Future<void> toggle() async {
    await setLanguage(state == AppLanguage.zh ? AppLanguage.en : AppLanguage.zh);
  }
}

final appLanguageProvider = NotifierProvider<AppLanguageNotifier, AppLanguage>(
  AppLanguageNotifier.new,
);
