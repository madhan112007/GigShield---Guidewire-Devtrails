import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:susanoo/providers/locale_provider.dart';
import 'package:susanoo/theme/app_theme.dart';

class ShellScreen extends ConsumerWidget {
  final Widget child;
  const ShellScreen({super.key, required this.child});

  int _locationIndex(BuildContext context) {
    final loc = GoRouterState.of(context).matchedLocation;
    if (loc.startsWith('/policy')) return 1;
    if (loc.startsWith('/claims')) return 2;
    if (loc.startsWith('/risk')) return 3;
    if (loc.startsWith('/profile')) return 4;
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final idx = _locationIndex(context);
    final s = ref.watch(stringsProvider);
    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: AppTheme.divider, width: 0.5)),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _NavItem(
                    icon: Icons.home_rounded,
                    label: s.home,
                    active: idx == 0,
                    onTap: () => context.go('/home')),
                _NavItem(
                    icon: Icons.shield_rounded,
                    label: s.policy,
                    active: idx == 1,
                    onTap: () => context.go('/policy')),
                _NavItem(
                    icon: Icons.receipt_long_rounded,
                    label: s.claims,
                    active: idx == 2,
                    onTap: () => context.go('/claims')),
                _NavItem(
                    icon: Icons.monitor_heart_rounded,
                    label: s.risk,
                    active: idx == 3,
                    onTap: () => context.go('/risk')),
                _NavItem(
                    icon: Icons.person_rounded,
                    label: s.profile,
                    active: idx == 4,
                    onTap: () => context.go('/profile')),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool active;
  final VoidCallback onTap;
  const _NavItem(
      {required this.icon,
      required this.label,
      required this.active,
      required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        behavior: HitTestBehavior.opaque,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: const EdgeInsets.symmetric(horizontal: 4),
          padding: const EdgeInsets.symmetric(vertical: 6),
          decoration: BoxDecoration(
            color: active ? AppTheme.primaryLight : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon,
                  color: active ? AppTheme.primary : AppTheme.textHint,
                  size: 24),
              const SizedBox(height: 2),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2),
                child: Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: active ? FontWeight.w600 : FontWeight.w400,
                    color: active ? AppTheme.primary : AppTheme.textHint,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
