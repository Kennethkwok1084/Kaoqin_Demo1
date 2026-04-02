import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:dio/dio.dart';

import '../../core/localization/app_locale.dart';
import '../../core/localization/app_strings.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/glass_panel.dart';
import 'providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _studentIdController = TextEditingController();
  final _passwordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _studentIdController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final success = await ref.read(authStateProvider.notifier).login(
          _studentIdController.text.trim(),
          _passwordController.text,
        );

    if (success && mounted) {
      context.go('/dashboard');
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.strings;
    final language = ref.watch(appLanguageProvider);
    final authState = ref.watch(authStateProvider);

    ref.listen<AsyncValue<Map<String, dynamic>?>>(authStateProvider, (previous, next) {
      if (next.hasError) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(_authErrorMessage(next.error, s))),
        );
      }
    });

    return Scaffold(
      body: Stack(
        children: [
          DecoratedBox(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color(0xFFF8FAFF),
                  Color(0xFFF2F2F7),
                  Color(0xFFEAF2FF),
                ],
              ),
            ),
            child: Center(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final compact = constraints.maxWidth < 900;

                  return ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1080),
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: compact
                          ? Column(
                              mainAxisSize: MainAxisSize.min,
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                const _LoginIntro(),
                                const SizedBox(height: 24),
                                _LoginForm(
                                  formKey: _formKey,
                                  studentIdController: _studentIdController,
                                  passwordController: _passwordController,
                                  authState: authState,
                                  onLogin: _handleLogin,
                                ),
                              ],
                            )
                          : Row(
                              children: [
                                const Expanded(
                                  child: Padding(
                                    padding: EdgeInsets.only(right: 28),
                                    child: _LoginIntro(),
                                  ),
                                ),
                                Expanded(
                                  child: _LoginForm(
                                    formKey: _formKey,
                                    studentIdController: _studentIdController,
                                    passwordController: _passwordController,
                                    authState: authState,
                                    onLogin: _handleLogin,
                                  ),
                                ),
                              ],
                            ),
                    ),
                  );
                },
              ),
            ),
          ),
          Positioned(
            top: 24,
            right: 24,
            child: FilledButton.tonalIcon(
              onPressed: () => ref.read(appLanguageProvider.notifier).toggle(),
              icon: const Icon(Icons.language_rounded),
              label: Text(language == AppLanguage.zh ? 'EN' : '中'),
            ),
          ),
        ],
      ),
    );
  }
}

String _authErrorMessage(Object? error, AppStrings s) {
  if (error is DioException) {
    final statusCode = error.response?.statusCode;
    if (statusCode == 401) {
      return s.invalidCredentials;
    }
    if (statusCode == 403) {
      return s.accountDisabled;
    }
    final serverMessage = error.response?.data;
    if (serverMessage is Map<String, dynamic>) {
      final message = serverMessage['message'] as String?;
      if (message != null && message.trim().isNotEmpty) {
        return '${s.loginFailed}: $message';
      }
    }
  }
  return '${s.loginFailed}: ${error ?? ''}';
}

class _LoginIntro extends StatelessWidget {
  const _LoginIntro();

  @override
  Widget build(BuildContext context) {
    final s = context.strings;

    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 64,
          height: 64,
          decoration: BoxDecoration(
            color: AppColors.accent,
            borderRadius: BorderRadius.circular(22),
            boxShadow: const [
              BoxShadow(
                color: Color(0x33007AFF),
                blurRadius: 24,
                offset: Offset(0, 14),
              ),
            ],
          ),
          child: const Icon(
            Icons.schedule_rounded,
            color: Colors.white,
            size: 30,
          ),
        ),
        const SizedBox(height: 24),
        Text(
          s.appTitle,
          style: Theme.of(context).textTheme.headlineLarge,
        ),
        const SizedBox(height: 12),
        Text(
          s.loginHeroSubtitle,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: AppColors.textSecondary,
              ),
        ),
        const SizedBox(height: 24),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            _FeaturePill(label: s.desktopShell),
            _FeaturePill(label: s.taskCenter),
            _FeaturePill(label: s.reportsAndHours),
          ],
        ),
      ],
    );
  }
}

class _LoginForm extends StatelessWidget {
  const _LoginForm({
    required this.formKey,
    required this.studentIdController,
    required this.passwordController,
    required this.authState,
    required this.onLogin,
  });

  final GlobalKey<FormState> formKey;
  final TextEditingController studentIdController;
  final TextEditingController passwordController;
  final AsyncValue<Map<String, dynamic>?> authState;
  final Future<void> Function() onLogin;

  @override
  Widget build(BuildContext context) {
    final s = context.strings;

    return GlassPanel(
      radius: 32,
      padding: const EdgeInsets.all(30),
      child: Form(
        key: formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              s.signIn,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              s.loginSubtitle,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
            const SizedBox(height: 24),
            TextFormField(
              controller: studentIdController,
              decoration: InputDecoration(
                labelText: s.accountHint,
                prefixIcon: const Icon(Icons.person_outline_rounded),
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return s.enterAccountId;
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: passwordController,
              obscureText: true,
              decoration: InputDecoration(
                labelText: s.passwordHint,
                prefixIcon: const Icon(Icons.lock_outline_rounded),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return s.enterPassword;
                }
                return null;
              },
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: authState.isLoading ? null : onLogin,
                child: authState.isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : Text(s.continueLabel),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FeaturePill extends StatelessWidget {
  const _FeaturePill({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surfaceStrong,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.borderStrong),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w700,
            ),
      ),
    );
  }
}
