import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:susanoo/l10n/app_strings.dart';
import 'package:susanoo/providers/locale_provider.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashAsync = ref.watch(dashboardProvider);

    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(
          title: Text(ref.watch(stringsProvider).profile),
          backgroundColor: Colors.white),
      body: dashAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (data) {
          final s = ref.watch(stringsProvider);
          final worker = data['worker'] as Map<String, dynamic>? ?? {};
          final name = worker['name'] as String? ?? 'Rider';
          final phone = worker['phone'] as String? ?? '';
          final city = worker['city'] as String? ?? '';
          final platform = (worker['platform'] as String?)?.toUpperCase() ?? '';
          final upi = worker['upi_id'] as String? ?? 'Not set';
          final avgEarnings =
              (worker['avg_daily_earnings'] as num?)?.toStringAsFixed(0) ??
                  '600';
          final riskScore =
              ((worker['risk_score'] as num?)?.toDouble() ?? 0.5) * 100;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: const BoxDecoration(
                      color: AppTheme.primaryLight, shape: BoxShape.circle),
                  child: Center(
                    child: Text(
                      name.isNotEmpty ? name[0].toUpperCase() : 'R',
                      style: const TextStyle(
                          fontSize: 36,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.primary),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text(name,
                    style: const TextStyle(
                        fontSize: 20, fontWeight: FontWeight.w700)),
                Text('$platform • $city',
                    style: const TextStyle(color: AppTheme.textSecondary)),
                const SizedBox(height: 24),
                _Section(title: s.accountDetails, tiles: [
                  _Tile(icon: Icons.phone, label: s.mobile, value: phone),
                  _Tile(
                      icon: Icons.account_balance_wallet_outlined,
                      label: s.upiId,
                      value: upi),
                  _Tile(icon: Icons.location_city, label: s.city, value: city),
                ]),
                const SizedBox(height: 16),
                _Section(title: s.riskProfile, tiles: [
                  _Tile(
                      icon: Icons.bar_chart,
                      label: s.avgDailyEarnings,
                      value: '₹$avgEarnings'),
                  _Tile(
                      icon: Icons.security,
                      label: s.riskScore,
                      value: '${riskScore.toInt()}/100'),
                ]),
                const SizedBox(height: 16),
                _LanguageSwitcher(),
                const SizedBox(height: 24),
                OutlinedButton.icon(
                  onPressed: () async {
                    await ref.read(authProvider.notifier).logout();
                    if (context.mounted) context.go('/auth/phone');
                  },
                  icon: const Icon(Icons.logout, color: AppTheme.danger),
                  label: Text(s.logout,
                      style: const TextStyle(color: AppTheme.danger)),
                  style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: AppTheme.danger)),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _LanguageSwitcher extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final currentLang = ref.watch(localeProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(s.language,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.divider, width: 0.5),
          ),
          child: Column(
            children: AppStrings.all.entries.map((entry) {
              final isSelected = entry.key == currentLang;
              return InkWell(
                onTap: () =>
                    ref.read(localeProvider.notifier).setLanguage(entry.key),
                borderRadius: BorderRadius.circular(16),
                child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  child: Row(
                    children: [
                      const Icon(Icons.language,
                          size: 20, color: AppTheme.textSecondary),
                      const SizedBox(width: 12),
                      Text(
                        entry.value.languageName,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight:
                              isSelected ? FontWeight.w700 : FontWeight.normal,
                          color: isSelected
                              ? AppTheme.primary
                              : AppTheme.textSecondary,
                        ),
                      ),
                      const Spacer(),
                      if (isSelected)
                        const Icon(Icons.check_circle_rounded,
                            color: AppTheme.primary, size: 20),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final List<Widget> tiles;
  const _Section({required this.title, required this.tiles});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.divider, width: 0.5),
          ),
          child: Column(children: tiles),
        ),
      ],
    );
  }
}

class _Tile extends StatelessWidget {
  final IconData icon;
  final String label, value;
  const _Tile({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppTheme.textSecondary),
          const SizedBox(width: 12),
          Text(label,
              style:
                  const TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
          const Spacer(),
          Text(value,
              style:
                  const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        ],
      ),
    );
  }
}
