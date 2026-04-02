import 'package:flutter/material.dart';

import 'apple_desktop_tokens.dart';

ThemeData buildAppleDesktopTheme() {
  final base = ThemeData.light(useMaterial3: true);

  return base.copyWith(
    scaffoldBackgroundColor: Colors.transparent,
    colorScheme: base.colorScheme.copyWith(
      primary: AppleDesktopTokens.accent,
      secondary: AppleDesktopTokens.accent,
      surface: AppleDesktopTokens.surfaceStrong,
      onSurface: AppleDesktopTokens.textPrimary,
      outline: AppleDesktopTokens.divider,
    ),
    textTheme: base.textTheme.copyWith(
      displaySmall: base.textTheme.displaySmall?.copyWith(
        fontWeight: FontWeight.w700,
        color: AppleDesktopTokens.textPrimary,
      ),
      headlineLarge: base.textTheme.headlineLarge?.copyWith(
        fontWeight: FontWeight.w700,
        color: AppleDesktopTokens.textPrimary,
      ),
      headlineMedium: base.textTheme.headlineMedium?.copyWith(
        fontWeight: FontWeight.w700,
        color: AppleDesktopTokens.textPrimary,
      ),
      titleLarge: base.textTheme.titleLarge?.copyWith(
        fontWeight: FontWeight.w700,
        color: AppleDesktopTokens.textPrimary,
      ),
      titleMedium: base.textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.w600,
        color: AppleDesktopTokens.textPrimary,
      ),
      bodyLarge: base.textTheme.bodyLarge?.copyWith(
        color: AppleDesktopTokens.textPrimary,
        height: 1.35,
      ),
      bodyMedium: base.textTheme.bodyMedium?.copyWith(
        color: AppleDesktopTokens.textSecondary,
        height: 1.35,
      ),
      bodySmall: base.textTheme.bodySmall?.copyWith(
        color: AppleDesktopTokens.textTertiary,
        height: 1.3,
      ),
    ),
    iconTheme: const IconThemeData(color: AppleDesktopTokens.textSecondary),
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.transparent,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      toolbarHeight: 72,
      foregroundColor: AppleDesktopTokens.textPrimary,
      iconTheme: IconThemeData(color: AppleDesktopTokens.textPrimary),
      titleTextStyle: TextStyle(
        color: AppleDesktopTokens.textPrimary,
        fontSize: 22,
        fontWeight: FontWeight.w700,
      ),
    ),
    cardTheme: CardThemeData(
      color: AppleDesktopTokens.surfaceStrong,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppleDesktopTokens.radiusL),
        side: const BorderSide(color: AppleDesktopTokens.divider),
      ),
      margin: EdgeInsets.zero,
    ),
    dividerTheme: const DividerThemeData(
      color: AppleDesktopTokens.divider,
      thickness: 1,
      space: 1,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppleDesktopTokens.surface,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      hintStyle: const TextStyle(color: AppleDesktopTokens.textTertiary),
      labelStyle: const TextStyle(color: AppleDesktopTokens.textSecondary),
      prefixIconColor: AppleDesktopTokens.textTertiary,
      suffixIconColor: AppleDesktopTokens.textTertiary,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppleDesktopTokens.radiusPill),
        borderSide: const BorderSide(color: AppleDesktopTokens.divider),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppleDesktopTokens.radiusPill),
        borderSide: const BorderSide(color: AppleDesktopTokens.divider),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppleDesktopTokens.radiusPill),
        borderSide: const BorderSide(color: AppleDesktopTokens.accent, width: 1.4),
      ),
    ),
    scrollbarTheme: ScrollbarThemeData(
      thumbColor: WidgetStateProperty.all(const Color(0x2C000000)),
      trackColor: WidgetStateProperty.all(Colors.transparent),
      radius: const Radius.circular(999),
      thickness: WidgetStateProperty.all(6),
    ),
  );
}
