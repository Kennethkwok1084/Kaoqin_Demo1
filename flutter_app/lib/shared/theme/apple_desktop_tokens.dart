import 'package:flutter/material.dart';

class AppleDesktopTokens {
  static const Color background = Color(0xFFF2F2F7);
  static const Color backgroundTint = Color(0xFFF8F8FC);
  static const Color surface = Color(0xEFFFFFFF);
  static const Color surfaceStrong = Color(0xFAFFFFFF);
  static const Color textPrimary = Color(0xFF111827);
  static const Color textSecondary = Color(0xFF6B7280);
  static const Color textTertiary = Color(0xFF9CA3AF);
  static const Color divider = Color(0x1A1F2937);
  static const Color border = Color(0x2AFFFFFF);
  static const Color accent = Color(0xFF007AFF);
  static const Color accentSoft = Color(0xFFEAF2FF);
  static const Color danger = Color(0xFFFF3B30);

  static const double sidebarWidth = 284;
  static const double desktopBreakpoint = 960;
  static const double radiusXL = 28;
  static const double radiusL = 24;
  static const double radiusM = 18;
  static const double radiusPill = 999;

  static List<BoxShadow> get softShadows => const [
        BoxShadow(
          color: Color(0x12000000),
          blurRadius: 28,
          offset: Offset(0, 14),
        ),
        BoxShadow(
          color: Color(0x0A000000),
          blurRadius: 3,
          offset: Offset(0, 1),
        ),
      ];

  static List<BoxShadow> get subtleShadows => const [
        BoxShadow(
          color: Color(0x0F000000),
          blurRadius: 18,
          offset: Offset(0, 8),
        ),
      ];

  static const LinearGradient accentGradient = LinearGradient(
    colors: <Color>[
      Color(0xFF5B7CFF),
      accent,
      Color(0xFF4F55E6),
    ],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient backgroundGradient = LinearGradient(
    colors: <Color>[
      background,
      backgroundTint,
      Color(0xFFFFFFFF),
    ],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}
