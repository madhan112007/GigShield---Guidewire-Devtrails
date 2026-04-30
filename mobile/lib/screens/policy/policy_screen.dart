import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:susanoo/providers/locale_provider.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/utils/constants.dart';

class PolicyScreen extends ConsumerWidget {
  const PolicyScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final policyAsync = ref.watch(activePolicyProvider);
    final s = ref.watch(stringsProvider);

    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(title: Text(s.myPolicy), backgroundColor: Colors.white),
      body: policyAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _NoPolicyView(s: s),
        data: (policy) => policy == null
            ? _NoPolicyView(s: s)
            : _ActivePolicyView(policy: policy),
      ),
    );
  }
}

class _NoPolicyView extends StatelessWidget {
  final dynamic s;
  const _NoPolicyView({required this.s});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: const BoxDecoration(
                  color: AppTheme.primaryLight, shape: BoxShape.circle),
              child: const Icon(Icons.shield_outlined,
                  size: 56, color: AppTheme.primary),
            ),
            const SizedBox(height: 24),
            Text(s.noActivePolicy,
                style:
                    const TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text(
              s.protectionDesc,
              style:
                  const TextStyle(color: AppTheme.textSecondary, fontSize: 15),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () => context.go('/policy/buy'),
              child: Text(s.buyWeeklyPolicy),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActivePolicyView extends ConsumerWidget {
  final Map<String, dynamic> policy;
  const _ActivePolicyView({required this.policy});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final tier = policy['tier'] as String? ?? '';
    final tierLabel = AppConstants.tierLabels[tier] ?? tier;
    final premium =
        (policy['weekly_premium'] as num?)?.toStringAsFixed(2) ?? '-';
    final maxDaily =
        (policy['max_daily_payout'] as num?)?.toStringAsFixed(0) ?? '-';
    final maxWeekly =
        (policy['max_weekly_payout'] as num?)?.toStringAsFixed(0) ?? '-';
    final totalClaimed =
        (policy['total_claimed'] as num?)?.toStringAsFixed(0) ?? '0';
    final claimsCount = policy['claims_count'] ?? 0;
    final startDate = policy['start_date'] != null
        ? DateFormat('dd MMM yyyy').format(DateTime.parse(policy['start_date']))
        : '-';
    final endDate = policy['end_date'] != null
        ? DateFormat('dd MMM yyyy').format(DateTime.parse(policy['end_date']))
        : '-';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Policy card
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF1A56DB), Color(0xFF0EA5E9)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.shield_rounded,
                        color: Colors.white, size: 24),
                    const SizedBox(width: 8),
                    Text(tierLabel,
                        style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w700,
                            fontSize: 18)),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(s.active.toUpperCase(),
                          style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w700,
                              fontSize: 12)),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Text('₹$premium/week',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 28,
                        fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                Text('$startDate → $endDate',
                    style: TextStyle(
                        color: Colors.white.withOpacity(0.8), fontSize: 13)),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // Coverage details
          Text(s.coverageDetails,
              style:
                  const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          _DetailRow(label: s.maxDailyPayout, value: '₹$maxDaily'),
          _DetailRow(label: s.maxWeeklyPayout, value: '₹$maxWeekly'),
          _DetailRow(label: s.totalClaimedThisWeek, value: '₹$totalClaimed'),
          _DetailRow(label: s.claimsThisWeek, value: '$claimsCount'),

          const SizedBox(height: 20),

          // Triggers covered
          Text(s.triggersCovered,
              style:
                  const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children:
                _getTriggers(tier).map((t) => Chip(label: Text(t))).toList(),
          ),

          const SizedBox(height: 20),
          OutlinedButton(
            onPressed: () => context.go('/policy/buy'),
            child: Text(s.renewChangePlan),
          ),
        ],
      ),
    );
  }

  List<String> _getTriggers(String tier) {
    switch (tier) {
      case 'basic':
        return ['Heavy Rain'];
      case 'smart':
        return ['Heavy Rain', 'Extreme Heat', 'AQI Spike'];
      case 'pro':
        return [
          'Heavy Rain',
          'Extreme Heat',
          'AQI Spike',
          'Traffic',
          'Emergency'
        ];
      default:
        return [];
    }
  }
}

class _DetailRow extends StatelessWidget {
  final String label, value;
  const _DetailRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.divider, width: 0.5),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style:
                  const TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
          Text(value,
              style:
                  const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
        ],
      ),
    );
  }
}
