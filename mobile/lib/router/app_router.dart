import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/screens/splash_screen.dart';
import 'package:susanoo/screens/onboarding/phone_screen.dart';
import 'package:susanoo/screens/onboarding/terms_screen.dart';
import 'package:susanoo/screens/onboarding/otp_screen.dart';
import 'package:susanoo/screens/onboarding/platform_screen.dart';
import 'package:susanoo/screens/onboarding/register_screen.dart';
import 'package:susanoo/screens/home/home_screen.dart';
import 'package:susanoo/screens/policy/policy_screen.dart';
import 'package:susanoo/screens/policy/buy_policy_screen.dart';
import 'package:susanoo/screens/claims/claims_screen.dart';
import 'package:susanoo/screens/profile/profile_screen.dart';
import 'package:susanoo/screens/risk/live_risk_screen.dart';
import 'package:susanoo/screens/shell_screen.dart';

// Bridges Riverpod state changes into a Listenable that GoRouter can watch
class _AuthListenable extends ChangeNotifier {
  _AuthListenable(this._ref) {
    _ref.listen<AuthState>(authProvider, (_, __) => notifyListeners());
  }
  final Ref _ref;
  bool get isLoggedIn => _ref.read(authProvider).isLoggedIn;
  bool get isNewUser => _ref.read(authProvider).isNewUser;
  bool get hasPlatform => _ref.read(authProvider).selectedPlatform != null;
}

final appRouterProvider = Provider<GoRouter>((ref) {
  final listenable = _AuthListenable(ref);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: listenable,
    redirect: (context, state) {
      final isLoggedIn = listenable.isLoggedIn;
      final isNewUser = listenable.isNewUser;
      final hasPlatform = listenable.hasPlatform;
      final loc = state.matchedLocation;
      final onSplash = loc == '/splash';
      final onAuth = loc.startsWith('/auth');
      final onPlatform = loc == '/auth/platform';
      final onRegister = loc == '/auth/register';

      if (onSplash) return null;
      if (isLoggedIn) return onAuth ? '/home' : null;
      // New user flow: platform first, then register
      if (isNewUser) {
        if (!hasPlatform) return onPlatform ? null : '/auth/platform';
        return onRegister ? null : '/auth/register';
      }
      if (!onAuth) return '/auth/phone';
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),
      GoRoute(path: '/auth/terms', builder: (_, __) => const TermsScreen()),
      GoRoute(path: '/auth/phone', builder: (_, __) => const PhoneScreen()),
      GoRoute(
        path: '/auth/otp',
        builder: (context, state) {
          final phone = state.extra as String? ?? '';
          return OtpScreen(phone: phone);
        },
      ),
      GoRoute(
        path: '/auth/platform',
        builder: (_, __) => const PlatformScreen(),
      ),
      GoRoute(
        path: '/auth/register',
        builder: (_, __) => const RegisterScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) => ShellScreen(child: child),
        routes: [
          GoRoute(path: '/home', builder: (_, __) => const HomeScreen()),
          GoRoute(path: '/policy', builder: (_, __) => const PolicyScreen()),
          GoRoute(
              path: '/policy/buy', builder: (_, __) => const BuyPolicyScreen()),
          GoRoute(path: '/claims', builder: (_, __) => const ClaimsScreen()),
          GoRoute(path: '/risk', builder: (_, __) => const LiveRiskScreen()),
          GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
        ],
      ),
    ],
  );
});
