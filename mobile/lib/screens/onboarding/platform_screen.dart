import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/utils/constants.dart';

class PlatformScreen extends ConsumerStatefulWidget {
  const PlatformScreen({super.key});

  @override
  ConsumerState<PlatformScreen> createState() => _PlatformScreenState();
}

class _PlatformScreenState extends ConsumerState<PlatformScreen> {
  String? _selected;
  _FetchState _fetchState = _FetchState.idle;
  Map<String, dynamic>? _earnings;

  Future<void> _onPlatformTap(String platform) async {
    setState(() {
      _selected = platform;
      _fetchState = _FetchState.fetching;
      _earnings = null;
    });

    try {
      final data =
          await ref.read(apiServiceProvider).getPlatformEarnings(platform);
      if (!mounted) return;
      setState(() {
        _earnings = data;
        _fetchState = _FetchState.done;
      });
    } catch (_) {
      if (!mounted) return;
      // Even if fetch fails, allow user to continue
      setState(() {
        _earnings = null;
        _fetchState = _FetchState.done;
      });
    }
  }

  void _continue() {
    if (_selected == null) return;
    ref.read(authProvider.notifier).setPlatform(_selected!);
    context.go('/auth/register');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(backgroundColor: Colors.white, elevation: 0),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 8),
              const Text('Which platform\ndo you deliver for?',
                  style: TextStyle(
                      fontSize: 26, fontWeight: FontWeight.w800, height: 1.25)),
              const SizedBox(height: 6),
              const Text(
                'We\'ll fetch your earnings directly from your platform.',
                style: TextStyle(color: AppTheme.textSecondary, fontSize: 14),
              ),
              const SizedBox(height: 28),

              // Platform grid
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: AppConstants.platforms.map((p) {
                  final isSelected = _selected == p['value'];
                  return GestureDetector(
                    onTap: () => _onPlatformTap(p['value']!),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 180),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 18, vertical: 12),
                      decoration: BoxDecoration(
                        color: isSelected ? AppTheme.primary : Colors.white,
                        border: Border.all(
                          color:
                              isSelected ? AppTheme.primary : AppTheme.divider,
                          width: isSelected ? 2 : 1,
                        ),
                        borderRadius: BorderRadius.circular(14),
                        boxShadow: isSelected
                            ? [
                                BoxShadow(
                                    color: AppTheme.primary.withOpacity(0.2),
                                    blurRadius: 8,
                                    offset: const Offset(0, 3))
                              ]
                            : [],
                      ),
                      child: Text(
                        p['label']!,
                        style: TextStyle(
                          color:
                              isSelected ? Colors.white : AppTheme.textPrimary,
                          fontWeight: FontWeight.w700,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),

              const SizedBox(height: 28),

              // Fetch state card
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 300),
                child: _buildFetchCard(),
              ),

              const Spacer(),

              // Continue button — only shown after fetch completes
              if (_fetchState == _FetchState.done && _selected != null)
                ElevatedButton(
                  onPressed: _continue,
                  child: const Text('Continue →'),
                ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFetchCard() {
    switch (_fetchState) {
      case _FetchState.idle:
        return const SizedBox.shrink();

      case _FetchState.fetching:
        final label = AppConstants.platforms.firstWhere(
            (p) => p['value'] == _selected,
            orElse: () => {'label': _selected!})['label']!;
        return _Card(
          key: const ValueKey('fetching'),
          color: AppTheme.primaryLight,
          child: Row(
            children: [
              const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                    strokeWidth: 2.5, color: AppTheme.primary),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Connecting to $label...',
                        style: const TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 14,
                            color: AppTheme.primary)),
                    const SizedBox(height: 2),
                    const Text('Fetching your earnings & delivery history',
                        style: TextStyle(
                            fontSize: 12, color: AppTheme.textSecondary)),
                  ],
                ),
              ),
            ],
          ),
        );

      case _FetchState.done:
        if (_earnings == null) {
          // Fetch failed but still allow continue
          return _Card(
            key: const ValueKey('done-no-data'),
            color: const Color(0xFFFFF8E1),
            border: const Color(0xFFFFE082),
            child: Row(
              children: [
                const Icon(Icons.info_outline_rounded,
                    color: Color(0xFFF59E0B), size: 18),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Could not fetch earnings right now. You can still continue.',
                    style: TextStyle(fontSize: 13, color: Color(0xFF78350F)),
                  ),
                ),
              ],
            ),
          );
        }
        final avg =
            (_earnings!['avg_daily_earnings'] as num?)?.toStringAsFixed(0) ??
                '—';
        final weekly =
            (_earnings!['weekly_settlement'] as num?)?.toStringAsFixed(0) ??
                '—';
        final days = _earnings!['active_days_last_week'] ?? '—';
        final label = _earnings!['platform_label'] as String? ?? _selected!;

        return _Card(
          key: const ValueKey('done'),
          color: const Color(0xFFF0FDF4),
          border: AppTheme.success.withOpacity(0.35),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.verified_rounded,
                      color: AppTheme.success, size: 18),
                  const SizedBox(width: 8),
                  Text('Details fetched from $label',
                      style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 14,
                          color: AppTheme.success)),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _EarningStat(
                      label: 'Avg Daily Earning',
                      value: '₹$avg',
                      icon: Icons.trending_up_rounded),
                  _EarningStat(
                      label: 'Last Week Payout',
                      value: '₹$weekly',
                      icon: Icons.account_balance_wallet_rounded),
                  _EarningStat(
                      label: 'Active Days',
                      value: '$days days',
                      icon: Icons.calendar_today_rounded),
                ],
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.shield_rounded,
                        color: AppTheme.primary, size: 16),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'If a disruption cuts your earnings, Susanoo pays you ₹$avg × disruption severity directly to your UPI.',
                        style: const TextStyle(
                            fontSize: 12, color: AppTheme.primary),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
    }
  }
}

enum _FetchState { idle, fetching, done }

class _Card extends StatelessWidget {
  final Widget child;
  final Color color;
  final Color? border;
  const _Card(
      {super.key, required this.child, required this.color, this.border});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(14),
        border: border != null ? Border.all(color: border!) : null,
      ),
      child: child,
    );
  }
}

class _EarningStat extends StatelessWidget {
  final String label, value;
  final IconData icon;
  const _EarningStat(
      {required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: AppTheme.success),
        const SizedBox(height: 4),
        Text(value,
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        Text(label,
            style:
                const TextStyle(fontSize: 10, color: AppTheme.textSecondary)),
      ],
    );
  }
}
