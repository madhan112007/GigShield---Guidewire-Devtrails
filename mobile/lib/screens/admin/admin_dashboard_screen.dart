import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/services/api_service.dart';
import 'package:susanoo/theme/app_theme.dart';

// ── Admin data providers ──────────────────────────────────────────────────────

final _adminStatsProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getAdminStats();
});

final _adminClaimsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getAdminClaims();
});

final _adminDisruptionsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getAdminDisruptions();
});

final _adminWorkersProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getAdminWorkers();
});

final _disbursementProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getAdminDisbursementRatio();
});

final _adminAnalyticsProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getAdminAnalytics();
});

// ── Main Screen ───────────────────────────────────────────────────────────────

class AdminDashboardScreen extends ConsumerStatefulWidget {
  const AdminDashboardScreen({super.key});

  @override
  ConsumerState<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends ConsumerState<AdminDashboardScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  int _selectedTab = 0;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 5, vsync: this);
    _tabs.addListener(() => setState(() => _selectedTab = _tabs.index));
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _logout() async {
    await ref.read(authProvider.notifier).logout();
    if (mounted) context.go('/auth/phone');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: SafeArea(
        child: Column(
          children: [
            _buildTopBar(),
            _buildTabBar(),
            Expanded(
              child: TabBarView(
                controller: _tabs,
                children: const [
                  _OverviewTab(),
                  _AnalyticsTab(),
                  _ClaimsTab(),
                  _DisruptionsTab(),
                  _WorkersTab(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.08))),
      ),
      child: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: Image.asset(
              'assets/images/susanoo_icon.jpg',
              width: 36,
              height: 36,
              fit: BoxFit.cover,
            ),
          ),
          const SizedBox(width: 12),
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Susanoo Admin', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 16)),
              Text('Operations Dashboard', style: TextStyle(color: Colors.white38, fontSize: 11, letterSpacing: 0.5)),
            ],
          ),
          const Spacer(),
          _LiveBadge(),
          const SizedBox(width: 12),
          GestureDetector(
            onTap: _logout,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(
                color: AppTheme.danger.withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppTheme.danger.withOpacity(0.3)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.logout_rounded, color: AppTheme.danger, size: 14),
                  SizedBox(width: 6),
                  Text('Logout', style: TextStyle(color: AppTheme.danger, fontSize: 12, fontWeight: FontWeight.w700)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabBar() {
    final tabs = ['Overview', 'Analytics', 'Claims', 'Disruptions', 'Workers'];
    final icons = [
      Icons.dashboard_rounded,
      Icons.bar_chart_rounded,
      Icons.receipt_long_rounded,
      Icons.bolt_rounded,
      Icons.people_rounded,
    ];
    return Container(
      color: const Color(0xFF0F172A),
      child: Row(
        children: List.generate(tabs.length, (i) {
          final active = _selectedTab == i;
          return Expanded(
            child: GestureDetector(
              onTap: () => _tabs.animateTo(i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  border: Border(
                    bottom: BorderSide(color: active ? AppTheme.primary : Colors.transparent, width: 2),
                  ),
                ),
                child: Column(
                  children: [
                    Icon(icons[i], size: 16, color: active ? AppTheme.primary : Colors.white38),
                    const SizedBox(height: 3),
                    Text(tabs[i], style: TextStyle(fontSize: 9, fontWeight: active ? FontWeight.w700 : FontWeight.w400, color: active ? AppTheme.primary : Colors.white38)),
                  ],
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}

// ── Live Badge ────────────────────────────────────────────────────────────────

class _LiveBadge extends StatefulWidget {
  @override
  State<_LiveBadge> createState() => _LiveBadgeState();
}

class _LiveBadgeState extends State<_LiveBadge> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(seconds: 1))..repeat(reverse: true);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, __) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: AppTheme.success.withOpacity(0.15),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppTheme.success.withOpacity(0.4)),
        ),
        child: Row(
          children: [
            Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                color: AppTheme.success.withOpacity(0.4 + _ctrl.value * 0.6),
                shape: BoxShape.circle,
                boxShadow: [BoxShadow(color: AppTheme.success.withOpacity(_ctrl.value * 0.6), blurRadius: 6)],
              ),
            ),
            const SizedBox(width: 6),
            const Text('LIVE', style: TextStyle(color: AppTheme.success, fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 1)),
          ],
        ),
      ),
    );
  }
}

// ── Overview Tab ──────────────────────────────────────────────────────────────

class _OverviewTab extends ConsumerWidget {
  const _OverviewTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(_adminStatsProvider);
    final disbAsync = ref.watch(_disbursementProvider);

    return RefreshIndicator(
      color: AppTheme.primary,
      backgroundColor: const Color(0xFF1E293B),
      onRefresh: () async {
        ref.invalidate(_adminStatsProvider);
        ref.invalidate(_disbursementProvider);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          disbAsync.when(
            data: (d) => _BCRPanel(data: d),
            loading: () => _DarkCard(child: const _Shimmer(height: 120)),
            error: (e, _) => _BCRPanel(data: const {}),
          ),
          const SizedBox(height: 16),
          statsAsync.when(
            data: (d) => _StatsGrid(metrics: d['metrics'] as Map<String, dynamic>? ?? {}),
            loading: () => _DarkCard(child: const _Shimmer(height: 160)),
            error: (e, _) => _StatsGrid(metrics: const {}),
          ),
          const SizedBox(height: 16),
          statsAsync.when(
            data: (d) => _ActiveDisruptionsPanel(disruptions: (d['active_disruptions'] as List?) ?? []),
            loading: () => _DarkCard(child: const _Shimmer(height: 100)),
            error: (_, __) => const SizedBox.shrink(),
          ),
          const SizedBox(height: 16),
          statsAsync.when(
            data: (d) => _WeeklyChartPanel(chart: (d['weekly_chart'] as List?) ?? []),
            loading: () => _DarkCard(child: const _Shimmer(height: 160)),
            error: (_, __) => const SizedBox.shrink(),
          ),
          const SizedBox(height: 16),
          statsAsync.when(
            data: (d) => _EligibilityPanel(summary: d['eligibility_summary'] as Map<String, dynamic>? ?? {}),
            loading: () => _DarkCard(child: const _Shimmer(height: 80)),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}

// ── BCR Panel ─────────────────────────────────────────────────────────────────

class _BCRPanel extends StatelessWidget {
  final Map<String, dynamic> data;
  const _BCRPanel({required this.data});

  String _fmt(double n) {
    if (n >= 10000000) return '₹${(n / 10000000).toStringAsFixed(1)}Cr';
    if (n >= 100000) return '₹${(n / 100000).toStringAsFixed(1)}L';
    if (n >= 1000) return '₹${(n / 1000).toStringAsFixed(1)}K';
    return '₹${n.toStringAsFixed(0)}';
  }

  @override
  Widget build(BuildContext context) {
    final overall = data['overall'] as Map<String, dynamic>? ?? {};
    final bcr = (overall['ratio'] as num?)?.toDouble() ?? 0.0;
    final status = overall['bcr_status'] as String? ?? 'insufficient_data';
    final premium = (overall['premium_collected'] as num?)?.toDouble() ?? 0.0;
    final disbursed = (overall['claims_disbursed'] as num?)?.toDouble() ?? 0.0;

    Color statusColor;
    String statusLabel;
    switch (status) {
      case 'healthy':
        statusColor = AppTheme.success;
        statusLabel = 'HEALTHY';
        break;
      case 'elevated':
        statusColor = AppTheme.warning;
        statusLabel = 'ELEVATED';
        break;
      case 'critical':
        statusColor = AppTheme.danger;
        statusLabel = 'CRITICAL';
        break;
      case 'low':
        statusColor = AppTheme.primary;
        statusLabel = 'LOW';
        break;
      default:
        statusColor = Colors.white38;
        statusLabel = 'NO DATA';
    }

    return _DarkCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Burning Cost Rate', style: TextStyle(color: Colors.white54, fontSize: 12, letterSpacing: 0.5)),
              _Chip(label: statusLabel, color: statusColor),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                bcr > 0 ? bcr.toStringAsFixed(2) : '—',
                style: TextStyle(color: statusColor, fontSize: 52, fontWeight: FontWeight.w900, height: 1),
              ),
              const SizedBox(width: 12),
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text('/ 1.00', style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 18)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: bcr.clamp(0.0, 1.0),
              minHeight: 10,
              backgroundColor: Colors.white10,
              valueColor: AlwaysStoppedAnimation<Color>(statusColor),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _MiniStat(label: 'Premium Collected', value: _fmt(premium)),
              const SizedBox(width: 16),
              _MiniStat(label: 'Claims Disbursed', value: _fmt(disbursed)),
              const SizedBox(width: 16),
              const _MiniStat(label: 'Target Range', value: '0.55 – 0.70'),
            ],
          ),
          if ((data['by_tier'] as List?)?.isNotEmpty == true) ...[
            const SizedBox(height: 16),
            const Text('By Tier', style: TextStyle(color: Colors.white38, fontSize: 11, letterSpacing: 0.5)),
            const SizedBox(height: 8),
            Row(
              children: (data['by_tier'] as List).map((t) {
                final tier = t as Map<String, dynamic>;
                final r = (tier['ratio'] as num?)?.toDouble() ?? 0.0;
                final name = (tier['tier'] as String? ?? '').toUpperCase();
                final color = name == 'PRO' ? AppTheme.success : name == 'SMART' ? AppTheme.primary : AppTheme.warning;
                return Expanded(
                  child: Container(
                    margin: const EdgeInsets.only(right: 8),
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: color.withOpacity(0.2)),
                    ),
                    child: Column(
                      children: [
                        Text(name, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w800)),
                        const SizedBox(height: 4),
                        Text('${(r * 100).toStringAsFixed(0)}%',
                            style: TextStyle(color: color, fontSize: 18, fontWeight: FontWeight.w900)),
                        Text('BCR', style: TextStyle(color: color.withOpacity(0.6), fontSize: 9)),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
          if ((data['by_city'] as List?)?.isNotEmpty == true) ...[
            const SizedBox(height: 16),
            const Text('By City', style: TextStyle(color: Colors.white38, fontSize: 11, letterSpacing: 0.5)),
            const SizedBox(height: 8),
            ...(data['by_city'] as List).map((c) {
              final city = c as Map<String, dynamic>;
              final r = (city['ratio'] as num?)?.toDouble() ?? 0.0;
              final cs = city['status'] as String? ?? '';
              final cc = cs == 'healthy' ? AppTheme.success : cs == 'critical' ? AppTheme.danger : AppTheme.warning;
              return Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  children: [
                    SizedBox(width: 90, child: Text(city['city'] as String? ?? '', style: const TextStyle(color: Colors.white70, fontSize: 12))),
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: r.clamp(0.0, 1.0),
                          minHeight: 6,
                          backgroundColor: Colors.white10,
                          valueColor: AlwaysStoppedAnimation<Color>(cc),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text('${(r * 100).toStringAsFixed(0)}%', style: TextStyle(color: cc, fontSize: 11, fontWeight: FontWeight.w700)),
                  ],
                ),
              );
            }),
          ],
        ],
      ),
    );
  }
}

// ── Stats Grid ────────────────────────────────────────────────────────────────

class _StatsGrid extends StatelessWidget {
  final Map<String, dynamic> metrics;
  const _StatsGrid({required this.metrics});

  String _fmtMoney(double n) {
    if (n >= 100000) return '₹${(n / 100000).toStringAsFixed(1)}L';
    if (n >= 1000) return '₹${(n / 1000).toStringAsFixed(1)}K';
    return '₹${n.toStringAsFixed(0)}';
  }

  @override
  Widget build(BuildContext context) {
    final workers = metrics['active_workers'] ?? 0;
    final policies = metrics['active_policies'] ?? 0;
    final claims = metrics['claims_this_week'] ?? 0;
    final payouts = (metrics['payouts_this_week'] as num?)?.toDouble() ?? 0.0;

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.6,
      children: [
        _StatCard(label: 'Active Workers', value: '$workers', icon: Icons.people_rounded, color: AppTheme.primary),
        _StatCard(label: 'Active Policies', value: '$policies', icon: Icons.shield_rounded, color: AppTheme.success),
        _StatCard(label: 'Claims (7 days)', value: '$claims', icon: Icons.receipt_long_rounded, color: AppTheme.warning),
        _StatCard(label: 'Payouts (7 days)', value: _fmtMoney(payouts), icon: Icons.payments_rounded, color: const Color(0xFF8B5CF6)),
      ],
    );
  }
}

// ── Active Disruptions Panel ──────────────────────────────────────────────────

class _ActiveDisruptionsPanel extends StatelessWidget {
  final List disruptions;
  const _ActiveDisruptionsPanel({required this.disruptions});

  @override
  Widget build(BuildContext context) {
    return _DarkCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.bolt_rounded, color: AppTheme.warning, size: 16),
              const SizedBox(width: 8),
              const Text('Live Disruptions', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
              const Spacer(),
              _Chip(label: '${disruptions.length} ACTIVE', color: disruptions.isEmpty ? Colors.white38 : AppTheme.warning),
            ],
          ),
          if (disruptions.isEmpty) ...[
            const SizedBox(height: 16),
            const Center(child: Text('All clear — no active disruptions', style: TextStyle(color: Colors.white38, fontSize: 13))),
          ] else ...[
            const SizedBox(height: 12),
            ...disruptions.take(5).map((d) {
              final m = d as Map<String, dynamic>;
              final sev = m['severity'] as String? ?? '';
              final sevColor = sev == 'extreme' ? AppTheme.danger : sev == 'severe' ? AppTheme.warning : AppTheme.primary;
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.04),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.white.withOpacity(0.06)),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(color: sevColor.withOpacity(0.15), borderRadius: BorderRadius.circular(8)),
                      child: Icon(Icons.bolt_rounded, color: sevColor, size: 16),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('${m['city']} • ${m['type']}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                          Text(sev.toUpperCase(), style: TextStyle(color: sevColor, fontSize: 10, fontWeight: FontWeight.w700)),
                        ],
                      ),
                    ),
                    Text('DSS ${(m['dss'] as num?)?.toStringAsFixed(2) ?? '—'}',
                        style: const TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.w700)),
                  ],
                ),
              );
            }),
          ],
        ],
      ),
    );
  }
}

// ── Eligibility Panel ─────────────────────────────────────────────────────────

class _EligibilityPanel extends StatelessWidget {
  final Map<String, dynamic> summary;
  const _EligibilityPanel({required this.summary});

  @override
  Widget build(BuildContext context) {
    final approved = (summary['auto_approved'] as num?)?.toInt() ?? 0;
    final review = (summary['under_review'] as num?)?.toInt() ?? 0;
    final rejected = (summary['auto_rejected'] as num?)?.toInt() ?? 0;
    final total = approved + review + rejected;

    return _DarkCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.verified_user_rounded, color: AppTheme.primary, size: 16),
              SizedBox(width: 8),
              Text('Eligibility Engine', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              _EligStat(label: 'Auto Approved', value: '$approved', color: AppTheme.success),
              const SizedBox(width: 12),
              _EligStat(label: 'Under Review', value: '$review', color: AppTheme.warning),
              const SizedBox(width: 12),
              _EligStat(label: 'Auto Rejected', value: '$rejected', color: AppTheme.danger),
            ],
          ),
          if (total > 0) ...[
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: Row(
                children: [
                  if (approved > 0) Expanded(flex: approved, child: Container(height: 8, color: AppTheme.success)),
                  if (review > 0) Expanded(flex: review, child: Container(height: 8, color: AppTheme.warning)),
                  if (rejected > 0) Expanded(flex: rejected, child: Container(height: 8, color: AppTheme.danger)),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ── Weekly Chart Panel ───────────────────────────────────────────────────────

class _WeeklyChartPanel extends StatelessWidget {
  final List chart;
  const _WeeklyChartPanel({required this.chart});

  @override
  Widget build(BuildContext context) {
    if (chart.isEmpty) return const SizedBox.shrink();
    return _DarkCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.bar_chart_rounded, color: AppTheme.primary, size: 16),
              SizedBox(width: 8),
              Text('7-Day Trend', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 120,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: chart.map((d) {
                final m = d as Map<String, dynamic>;
                final claims = (m['claims'] as num?)?.toInt() ?? 0;
                final payouts = (m['payouts'] as num?)?.toDouble() ?? 0.0;
                final maxVal = chart.fold<double>(1, (prev, e) {
                  final c = (e as Map)['claims'] as num? ?? 0;
                  return c.toDouble() > prev ? c.toDouble() : prev;
                });
                final barH = claims / maxVal;
                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Text('$claims', style: const TextStyle(color: Colors.white54, fontSize: 8)),
                        const SizedBox(height: 2),
                        Container(
                          height: 80 * barH,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [AppTheme.primary, Color(0xFF10B981)],
                              begin: Alignment.bottomCenter,
                              end: Alignment.topCenter,
                            ),
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(m['day'] as String? ?? '', style: const TextStyle(color: Colors.white38, fontSize: 9)),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Analytics Tab ─────────────────────────────────────────────────────────────

class _AnalyticsTab extends ConsumerWidget {
  const _AnalyticsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analyticsAsync = ref.watch(_adminAnalyticsProvider);
    final disbAsync = ref.watch(_disbursementProvider);

    return RefreshIndicator(
      color: AppTheme.primary,
      backgroundColor: const Color(0xFF1E293B),
      onRefresh: () async {
        ref.invalidate(_adminAnalyticsProvider);
        ref.invalidate(_disbursementProvider);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Next-week forecast
          analyticsAsync.when(
            data: (d) => _ForecastPanel(forecast: (d['next_week_forecast'] as List?) ?? []),
            loading: () => _DarkCard(child: const _Shimmer(height: 160)),
            error: (_, __) => const SizedBox.shrink(),
          ),
          const SizedBox(height: 16),
          // City loss ratios
          analyticsAsync.when(
            data: (d) => _CityLossPanel(cities: (d['city_loss_ratios'] as List?) ?? []),
            loading: () => _DarkCard(child: const _Shimmer(height: 200)),
            error: (_, __) => const SizedBox.shrink(),
          ),
          const SizedBox(height: 16),
          // Stress test
          analyticsAsync.when(
            data: (d) => _StressTestPanel(stress: d['stress_test'] as Map<String, dynamic>? ?? {}),
            loading: () => _DarkCard(child: const _Shimmer(height: 120)),
            error: (_, __) => const SizedBox.shrink(),
          ),
          const SizedBox(height: 16),
          // Eligibility trend
          analyticsAsync.when(
            data: (d) => _EligibilityTrendPanel(trend: (d['eligibility_trend'] as List?) ?? []),
            loading: () => _DarkCard(child: const _Shimmer(height: 120)),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}

class _ForecastPanel extends StatelessWidget {
  final List forecast;
  const _ForecastPanel({required this.forecast});

  @override
  Widget build(BuildContext context) {
    return _DarkCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.trending_up_rounded, color: AppTheme.success, size: 16),
              SizedBox(width: 8),
              Text('Next Week Forecast', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 4),
          const Text('Estimated claims by city based on trigger probabilities',
              style: TextStyle(color: Colors.white38, fontSize: 11)),
          const SizedBox(height: 14),
          if (forecast.isEmpty)
            const Text('No active cities', style: TextStyle(color: Colors.white38, fontSize: 13))
          else
            ...forecast.map((f) {
              final m = f as Map<String, dynamic>;
              final city = m['city'] as String? ?? '';
              final atRisk = (m['workers_at_risk'] as num?)?.toInt() ?? 0;
              final estClaims = (m['estimated_claims'] as num?)?.toInt() ?? 0;
              final topRisks = (m['top_risks'] as List?) ?? [];
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.04),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.white.withOpacity(0.06)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(city, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
                          const SizedBox(height: 4),
                          Text(
                            topRisks.map((r) {
                              final rm = r as Map<String, dynamic>;
                              return '${rm['peril']} ${rm['probability']}%';
                            }).join(' • '),
                            style: const TextStyle(color: Colors.white38, fontSize: 10),
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text('~$estClaims claims', style: const TextStyle(color: AppTheme.warning, fontWeight: FontWeight.w700, fontSize: 13)),
                        Text('$atRisk at risk', style: const TextStyle(color: Colors.white38, fontSize: 10)),
                      ],
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }
}

class _CityLossPanel extends StatelessWidget {
  final List cities;
  const _CityLossPanel({required this.cities});

  @override
  Widget build(BuildContext context) {
    return _DarkCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.location_city_rounded, color: AppTheme.warning, size: 16),
              SizedBox(width: 8),
              Text('City Loss Ratios', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 4),
          const Text('Claims paid vs premium collected per city',
              style: TextStyle(color: Colors.white38, fontSize: 11)),
          const SizedBox(height: 14),
          if (cities.isEmpty)
            const Text('No data yet', style: TextStyle(color: Colors.white38, fontSize: 13))
          else
            ...cities.map((c) {
              final m = c as Map<String, dynamic>;
              final city = m['city'] as String? ?? '';
              final ratio = (m['loss_ratio'] as num?)?.toDouble() ?? 0.0;
              final paid = (m['paid'] as num?)?.toDouble() ?? 0.0;
              final premium = (m['premium'] as num?)?.toDouble() ?? 0.0;
              final color = ratio > 0.85 ? AppTheme.danger : ratio > 0.70 ? AppTheme.warning : ratio > 0.55 ? AppTheme.success : AppTheme.primary;
              final label = ratio > 0.85 ? 'CRITICAL' : ratio > 0.70 ? 'ELEVATED' : ratio > 0.55 ? 'HEALTHY' : 'LOW';
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(child: Text(city, style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w600))),
                        _Chip(label: label, color: color),
                        const SizedBox(width: 8),
                        Text('${(ratio * 100).toStringAsFixed(0)}%', style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w800)),
                      ],
                    ),
                    const SizedBox(height: 4),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: ratio.clamp(0.0, 1.0),
                        minHeight: 6,
                        backgroundColor: Colors.white10,
                        valueColor: AlwaysStoppedAnimation<Color>(color),
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text('Paid ₹${paid.toStringAsFixed(0)} / Collected ₹${premium.toStringAsFixed(0)}',
                        style: const TextStyle(color: Colors.white24, fontSize: 9)),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }
}

class _StressTestPanel extends StatelessWidget {
  final Map<String, dynamic> stress;
  const _StressTestPanel({required this.stress});

  @override
  Widget build(BuildContext context) {
    if (stress.isEmpty) return const SizedBox.shrink();
    final verdict = stress['verdict'] as String? ?? '';
    final stressBcr = (stress['stress_bcr'] as num?)?.toDouble() ?? 0.0;
    final triggerDays = stress['expected_trigger_days'];
    final maxLiability = (stress['max_liability_per_worker'] as num?)?.toDouble() ?? 0.0;
    final isSolvent = verdict == 'SOLVENT';

    return _DarkCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.thunderstorm_rounded, color: isSolvent ? AppTheme.success : AppTheme.danger, size: 16),
              const SizedBox(width: 8),
              const Text('14-Day Monsoon Stress Test', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
              const Spacer(),
              _Chip(label: verdict, color: isSolvent ? AppTheme.success : AppTheme.danger),
            ],
          ),
          const SizedBox(height: 4),
          const Text('Worst-case payout liability per worker in a 14-day monsoon',
              style: TextStyle(color: Colors.white38, fontSize: 11)),
          const SizedBox(height: 14),
          Row(
            children: [
              _MiniStat(label: 'Stress BCR', value: stressBcr.toStringAsFixed(2)),
              const SizedBox(width: 16),
              _MiniStat(label: 'Trigger Days', value: '$triggerDays'),
              const SizedBox(width: 16),
              _MiniStat(label: 'Max Liability', value: '₹${maxLiability.toStringAsFixed(0)}'),
            ],
          ),
        ],
      ),
    );
  }
}

class _EligibilityTrendPanel extends StatelessWidget {
  final List trend;
  const _EligibilityTrendPanel({required this.trend});

  @override
  Widget build(BuildContext context) {
    if (trend.isEmpty) return const SizedBox.shrink();
    final maxFlagged = trend.fold<int>(1, (prev, e) {
      final f = (e as Map)['flagged'] as num? ?? 0;
      return f.toInt() > prev ? f.toInt() : prev;
    });
    return _DarkCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.verified_user_rounded, color: AppTheme.danger, size: 16),
              SizedBox(width: 8),
              Text('Eligibility Flags (7 Days)', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 14),
          SizedBox(
            height: 80,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: trend.map((d) {
                final m = d as Map<String, dynamic>;
                final flagged = (m['flagged'] as num?)?.toInt() ?? 0;
                final barH = flagged / maxFlagged;
                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        if (flagged > 0)
                          Text('$flagged', style: const TextStyle(color: Colors.white54, fontSize: 8)),
                        const SizedBox(height: 2),
                        Container(
                          height: flagged == 0 ? 4 : 60 * barH,
                          decoration: BoxDecoration(
                            color: flagged == 0 ? Colors.white10 : AppTheme.danger.withOpacity(0.7),
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(m['day'] as String? ?? '', style: const TextStyle(color: Colors.white38, fontSize: 9)),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Claims Tab ────────────────────────────────────────────────────────────────

class _ClaimsTab extends ConsumerWidget {
  const _ClaimsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final claimsAsync = ref.watch(_adminClaimsProvider);

    return RefreshIndicator(
      color: AppTheme.primary,
      backgroundColor: const Color(0xFF1E293B),
      onRefresh: () async => ref.invalidate(_adminClaimsProvider),
      child: claimsAsync.when(
        data: (claims) => claims.isEmpty
            ? const Center(child: Text('No claims yet', style: TextStyle(color: Colors.white38)))
            : ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: claims.length,
                itemBuilder: (_, i) => _ClaimCard(claim: claims[i] as Map<String, dynamic>),
              ),
        loading: () => ListView(
          padding: const EdgeInsets.all(16),
          children: List.generate(5, (_) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: _DarkCard(child: const _Shimmer(height: 70)),
          )),
        ),
        error: (e, _) => Center(child: Text('Error: $e', style: const TextStyle(color: AppTheme.danger))),
      ),
    );
  }
}

class _ClaimCard extends StatefulWidget {
  final Map<String, dynamic> claim;
  const _ClaimCard({required this.claim});

  @override
  State<_ClaimCard> createState() => _ClaimCardState();
}

class _ClaimCardState extends State<_ClaimCard> {
  bool _expanded = false;
  bool _loading = false;
  Map<String, dynamic>? _investigation;
  String? _error;

  Future<void> _runInvestigation(BuildContext context, WidgetRef ref) async {
    setState(() { _loading = true; _error = null; });
    try {
      final api = ref.read(apiServiceProvider);
      final result = await api.investigateClaim(widget.claim['id'] as String);
      setState(() {
        _investigation = result['investigation'] as Map<String, dynamic>?;
        _loading = false;
        _expanded = true;
      });
      ref.invalidate(_adminClaimsProvider);
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Future<void> _override(BuildContext context, WidgetRef ref, String action) async {
    final reasonCtrl = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: Text(
          '${action == 'approve' ? 'Approve' : 'Reject'} Claim',
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
        ),
        content: TextField(
          controller: reasonCtrl,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: 'Reason (optional)',
            hintStyle: const TextStyle(color: Colors.white38),
            enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
            focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: AppTheme.primary)),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel', style: TextStyle(color: Colors.white38))),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(action == 'approve' ? 'Approve' : 'Reject',
                style: TextStyle(color: action == 'approve' ? AppTheme.success : AppTheme.danger, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    setState(() => _loading = true);
    try {
      final api = ref.read(apiServiceProvider);
      await api.overrideClaim(
        widget.claim['id'] as String,
        action,
        reasonCtrl.text.isEmpty ? 'Manual admin override' : reasonCtrl.text,
      );
      ref.invalidate(_adminClaimsProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Claim ${action == 'approve' ? 'approved' : 'rejected'} successfully'),
          backgroundColor: action == 'approve' ? AppTheme.success : AppTheme.danger,
        ));
      }
    } catch (e) {
      setState(() { _error = e.toString(); });
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer(
      builder: (context, ref, _) {
        final claim = widget.claim;
        final score = (claim['eligibility_score'] as num?)?.toInt() ?? 0;
        final status = claim['status'] as String? ?? '';
        final scoreColor = score > 70 ? AppTheme.danger : score > 30 ? AppTheme.warning : AppTheme.success;
        final statusColor = status == 'paid'
            ? AppTheme.success
            : status == 'approved'
                ? AppTheme.primary
                : status == 'rejected'
                    ? AppTheme.danger
                    : AppTheme.warning;
        final isPending = status == 'pending';
        final needsInvestigation = isPending && score >= 30;

        // Parse stored investigation if available
        final storedInvestigation = _investigation;
        final steps = (storedInvestigation?['steps'] as List?)?.cast<Map<String, dynamic>>();
        final verdict = storedInvestigation?['verdict'] as String?;
        final confidence = (storedInvestigation?['confidence'] as num?)?.toInt();
        final explanation = storedInvestigation?['explanation'] as String?;
        final penalty = (storedInvestigation?['penalty'] as num?)?.toInt() ?? 0;

        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.05),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: needsInvestigation && storedInvestigation == null
                  ? AppTheme.warning.withOpacity(0.4)
                  : Colors.white.withOpacity(0.08),
            ),
          ),
          child: Column(
            children: [
              // ── Main row ──────────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(color: scoreColor.withOpacity(0.15), borderRadius: BorderRadius.circular(10)),
                      child: Center(child: Text('$score', style: TextStyle(color: scoreColor, fontWeight: FontWeight.w800, fontSize: 13))),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(claim['worker'] as String? ?? '—', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
                          Text('${claim['city'] ?? ''} • ${claim['event'] ?? ''}', style: const TextStyle(color: Colors.white38, fontSize: 11)),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(claim['amount'] as String? ?? '—', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
                        const SizedBox(height: 4),
                        _Chip(label: status.toUpperCase(), color: statusColor),
                      ],
                    ),
                  ],
                ),
              ),

              // ── AI Investigation panel (only for pending + score >= 30) ──
              if (needsInvestigation || storedInvestigation != null) ...[
                Container(
                  margin: const EdgeInsets.fromLTRB(14, 0, 14, 14),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F172A),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.primary.withOpacity(0.2)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Header row
                      Row(
                        children: [
                          const Icon(Icons.smart_toy_rounded, color: AppTheme.primary, size: 14),
                          const SizedBox(width: 6),
                          const Text('Agentic AI Investigation',
                              style: TextStyle(color: AppTheme.primary, fontSize: 12, fontWeight: FontWeight.w700)),
                          const Spacer(),
                          if (storedInvestigation != null)
                            GestureDetector(
                              onTap: () => setState(() => _expanded = !_expanded),
                              child: Icon(
                                _expanded ? Icons.expand_less_rounded : Icons.expand_more_rounded,
                                color: Colors.white38, size: 18,
                              ),
                            ),
                        ],
                      ),

                      // Verdict summary (always visible once investigated)
                      if (verdict != null) ...[
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            _Chip(
                              label: verdict,
                              color: verdict == 'APPROVED' ? AppTheme.success : AppTheme.danger,
                            ),
                            const SizedBox(width: 8),
                            Text('Confidence: $confidence%',
                                style: const TextStyle(color: Colors.white54, fontSize: 11)),
                            if (penalty > 0) ...[
                              const SizedBox(width: 8),
                              _Chip(label: '+$penalty penalty', color: AppTheme.danger),
                            ],
                          ],
                        ),
                      ],

                      // Expanded steps
                      if (_expanded && steps != null) ...[
                        const SizedBox(height: 10),
                        ...steps.map((s) {
                          final passed = s['passed'] as bool? ?? false;
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 6),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(passed ? '✅' : '❌', style: const TextStyle(fontSize: 12)),
                                const SizedBox(width: 6),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(s['step'] as String? ?? '',
                                          style: TextStyle(
                                              color: passed ? AppTheme.success : AppTheme.danger,
                                              fontSize: 11, fontWeight: FontWeight.w700)),
                                      Text(s['result'] as String? ?? '',
                                          style: const TextStyle(color: Colors.white54, fontSize: 10)),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        }),
                      ],

                      if (_error != null) ...[
                        const SizedBox(height: 8),
                        Text(_error!, style: const TextStyle(color: AppTheme.danger, fontSize: 10)),
                      ],

                      const SizedBox(height: 10),

                      // Action buttons
                      if (isPending) Row(
                        children: [
                          if (storedInvestigation == null)
                            Expanded(
                              child: GestureDetector(
                                onTap: _loading ? null : () => _runInvestigation(context, ref),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(vertical: 8),
                                  decoration: BoxDecoration(
                                    color: AppTheme.primary.withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(color: AppTheme.primary.withOpacity(0.4)),
                                  ),
                                  child: Center(
                                    child: _loading
                                        ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary))
                                        : const Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              Icon(Icons.smart_toy_rounded, color: AppTheme.primary, size: 13),
                                              SizedBox(width: 5),
                                              Text('Run AI Investigation', style: TextStyle(color: AppTheme.primary, fontSize: 11, fontWeight: FontWeight.w700)),
                                            ],
                                          ),
                                  ),
                                ),
                              ),
                            )
                          else ...[
                            Expanded(
                              child: GestureDetector(
                                onTap: _loading ? null : () => _override(context, ref, 'approve'),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(vertical: 8),
                                  decoration: BoxDecoration(
                                    color: AppTheme.success.withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(color: AppTheme.success.withOpacity(0.4)),
                                  ),
                                  child: const Center(
                                    child: Text('✓ Approve', style: TextStyle(color: AppTheme.success, fontSize: 11, fontWeight: FontWeight.w700)),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: GestureDetector(
                                onTap: _loading ? null : () => _override(context, ref, 'reject'),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(vertical: 8),
                                  decoration: BoxDecoration(
                                    color: AppTheme.danger.withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(color: AppTheme.danger.withOpacity(0.4)),
                                  ),
                                  child: const Center(
                                    child: Text('✗ Reject', style: TextStyle(color: AppTheme.danger, fontSize: 11, fontWeight: FontWeight.w700)),
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}

// ── Disruptions Tab ───────────────────────────────────────────────────────────

class _DisruptionsTab extends ConsumerWidget {
  const _DisruptionsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(_adminDisruptionsProvider);

    return RefreshIndicator(
      color: AppTheme.primary,
      backgroundColor: const Color(0xFF1E293B),
      onRefresh: () async => ref.invalidate(_adminDisruptionsProvider),
      child: async.when(
        data: (list) => list.isEmpty
            ? const Center(child: Text('No disruption events', style: TextStyle(color: Colors.white38)))
            : ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: list.length,
                itemBuilder: (_, i) => _DisruptionCard(d: list[i] as Map<String, dynamic>),
              ),
        loading: () => ListView(
          padding: const EdgeInsets.all(16),
          children: List.generate(4, (_) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: _DarkCard(child: const _Shimmer(height: 60)),
          )),
        ),
        error: (e, _) => Center(child: Text('Error: $e', style: const TextStyle(color: AppTheme.danger))),
      ),
    );
  }
}

class _DisruptionCard extends StatelessWidget {
  final Map<String, dynamic> d;
  const _DisruptionCard({required this.d});

  @override
  Widget build(BuildContext context) {
    final sev = d['severity'] as String? ?? '';
    final active = d['active'] as bool? ?? false;
    final sevColor = sev == 'extreme' ? AppTheme.danger : sev == 'severe' ? AppTheme.warning : AppTheme.primary;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: active ? sevColor.withOpacity(0.3) : Colors.white.withOpacity(0.06)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(color: sevColor.withOpacity(0.15), borderRadius: BorderRadius.circular(10)),
            child: Icon(Icons.bolt_rounded, color: sevColor, size: 18),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${d['city']} • ${d['type']}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
                Text(sev.toUpperCase(), style: TextStyle(color: sevColor, fontSize: 10, fontWeight: FontWeight.w700)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('DSS ${(d['dss'] as num?)?.toStringAsFixed(2) ?? '—'}',
                  style: const TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              _Chip(label: active ? 'LIVE' : 'ENDED', color: active ? AppTheme.success : Colors.white38),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Workers Tab ───────────────────────────────────────────────────────────────

class _WorkersTab extends ConsumerWidget {
  const _WorkersTab();
    @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(_adminWorkersProvider);

    return RefreshIndicator(
      color: AppTheme.primary,
      backgroundColor: const Color(0xFF1E293B),
      onRefresh: () async => ref.invalidate(_adminWorkersProvider),
      child: async.when(
        data: (list) => list.isEmpty
            ? const Center(child: Text('No workers found', style: TextStyle(color: Colors.white38)))
            : ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: list.length,
                itemBuilder: (_, i) => _WorkerCard(w: list[i] as Map<String, dynamic>),
              ),
        loading: () => ListView(
          padding: const EdgeInsets.all(16),
          children: List.generate(5, (_) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: _DarkCard(child: const _Shimmer(height: 60)),
          )),
        ),
        error: (e, _) => Center(child: Text('Error: $e', style: const TextStyle(color: AppTheme.danger))),
      ),
    );
  }
}

class _WorkerCard extends StatelessWidget {
  final Map<String, dynamic> w;
  const _WorkerCard({required this.w});

  @override
  Widget build(BuildContext context) {
    final risk = (w['risk_score'] as num?)?.toDouble() ?? 0.0;
    final active = w['is_active'] as bool? ?? false;
    final riskColor = risk > 0.7 ? AppTheme.danger : risk > 0.4 ? AppTheme.warning : AppTheme.success;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AppTheme.primary.withOpacity(0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.person_rounded, color: AppTheme.primary, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(w['name'] as String? ?? '—',
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
                Text(
                  '${(w['platform'] as String? ?? '').replaceAll('_', ' ').toUpperCase()} • ${w['city'] ?? ''}',
                  style: const TextStyle(color: Colors.white38, fontSize: 11),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('Risk ${(risk * 100).toStringAsFixed(0)}%',
                  style: TextStyle(color: riskColor, fontWeight: FontWeight.w700, fontSize: 12)),
              const SizedBox(height: 4),
              if ((w['penalty_score'] as num? ?? 0) > 0)
                Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: _Chip(label: 'Penalty ${(w['penalty_score'] as num).toInt()}', color: AppTheme.danger),
                ),
              _Chip(label: active ? 'ACTIVE' : 'OFFLINE', color: active ? AppTheme.success : Colors.white38),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Shared Widgets ────────────────────────────────────────────────────────────

class _DarkCard extends StatelessWidget {
  final Widget child;
  const _DarkCard({required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: child,
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label, value;
  final IconData icon;
  final Color color;
  const _StatCard({required this.label, required this.value, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 20),
          const Spacer(),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
          Text(label, style: const TextStyle(color: Colors.white38, fontSize: 11)),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final Color color;
  const _Chip({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 0.5)),
    );
  }
}

class _MiniStat extends StatelessWidget {
  final String label, value;
  const _MiniStat({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
        Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10)),
      ],
    );
  }
}

class _EligStat extends StatelessWidget {
  final String label, value;
  final Color color;
  const _EligStat({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(color: color, fontSize: 22, fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10), textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}

class _Shimmer extends StatefulWidget {
  final double height;
  const _Shimmer({required this.height});

  @override
  State<_Shimmer> createState() => _ShimmerState();
}

class _ShimmerState extends State<_Shimmer> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200))..repeat();
    _anim = Tween<double>(begin: -1.0, end: 2.0).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (_, __) => Container(
        height: widget.height,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          gradient: LinearGradient(
            begin: Alignment(_anim.value - 1, 0),
            end: Alignment(_anim.value, 0),
            colors: [
              Colors.white.withOpacity(0.04),
              Colors.white.withOpacity(0.10),
              Colors.white.withOpacity(0.04),
            ],
          ),
        ),
      ),
    );
  }
}
