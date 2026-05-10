import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:susanoo/providers/locale_provider.dart';
import 'package:susanoo/l10n/app_strings.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/utils/constants.dart';

void _showNotifications(
    BuildContext context, WidgetRef ref, List<dynamic> notifs) {
  showModalBottomSheet(
    context: context,
    shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
    builder: (_) => Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
          child: Row(
            children: [
              const Text('Notifications',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
              const Spacer(),
              if (notifs.any((n) => n['is_read'] == false))
                TextButton(
                  onPressed: () async {
                    await ref
                        .read(apiServiceProvider)
                        .markAllNotificationsRead();
                    ref.invalidate(notificationsProvider);
                    if (context.mounted) Navigator.pop(context);
                  },
                  child: const Text('Mark all read'),
                ),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: notifs.isEmpty
              ? const Center(
                  child: Text('No notifications yet',
                      style: TextStyle(color: Colors.grey)))
              : ListView.separated(
                  itemCount: notifs.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (_, i) {
                    final n = notifs[i] as Map<String, dynamic>;
                    final isRead = n['is_read'] == true;
                    return ListTile(
                      leading: CircleAvatar(
                        backgroundColor: isRead
                            ? Colors.grey.shade100
                            : AppTheme.primaryLight,
                        child: Icon(
                          _notifIcon(n['notif_type'] as String? ?? ''),
                          color: isRead ? Colors.grey : AppTheme.primary,
                          size: 18,
                        ),
                      ),
                      title: Text(n['title'] ?? '',
                          style: TextStyle(
                              fontWeight:
                                  isRead ? FontWeight.w400 : FontWeight.w700,
                              fontSize: 14)),
                      subtitle: Text(n['body'] ?? '',
                          style: const TextStyle(fontSize: 12)),
                      tileColor: isRead
                          ? null
                          : AppTheme.primaryLight.withOpacity(0.3),
                      onTap: () async {
                        await ref
                            .read(apiServiceProvider)
                            .markNotificationRead(n['id'] as String);
                        ref.invalidate(notificationsProvider);
                      },
                    );
                  },
                ),
        ),
      ],
    ),
  );
}

IconData _notifIcon(String type) {
  switch (type) {
    case 'claim_approved':
      return Icons.thumb_up_rounded;
    case 'claim_paid':
      return Icons.payments_rounded;
    case 'claim_rejected':
      return Icons.cancel_rounded;
    case 'disruption_detected':
      return Icons.warning_rounded;
    case 'policy_expiring':
      return Icons.timer_rounded;
    default:
      return Icons.notifications_rounded;
  }
}

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashAsync = ref.watch(dashboardProvider);

    return Scaffold(
      backgroundColor: AppTheme.surface,
      body: dashAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (data) {
          final s = ref.watch(stringsProvider);
          final worker = data['worker'] as Map<String, dynamic>? ?? {};
          final policy = data['active_policy'] as Map<String, dynamic>?;
          final disruptions =
              data['active_disruptions'] as List<dynamic>? ?? [];
          final claims = data['recent_claims'] as List<dynamic>? ?? [];
          final totalProtected =
              (data['total_earned_protection'] as num?)?.toDouble() ?? 0.0;

          final workerName = (worker['name'] as String?)?.split(' ').first ?? 'Rider';
          final workerCity = worker['city'] as String? ?? '';
          final workerPlatform = (worker['platform'] as String?)?.toUpperCase() ?? '';

          return CustomScrollView(
            slivers: [
              _buildAppBar(context, workerName, workerCity, workerPlatform, s),
              SliverPadding(
                padding: const EdgeInsets.all(20),
                sliver: SliverList(
                  delegate: SliverChildListDelegate([
                    // Shield status card
                    _ShieldCard(
                        policy: policy, onTap: () => context.go('/policy')),
                    const SizedBox(height: 16),

                    // Stats row
                    Row(
                      children: [
                        Expanded(
                            child: _StatCard(
                          label: s.policy,
                          value: '₹${totalProtected.toStringAsFixed(0)}',
                          icon: Icons.savings_rounded,
                          color: AppTheme.success,
                        )),
                        const SizedBox(width: 12),
                        Expanded(
                            child: _StatCard(
                          label: s.claims,
                          value: '${claims.length}',
                          icon: Icons.receipt_long_rounded,
                          color: AppTheme.primary,
                        )),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // ── My Dashboard button ───────────────────────────────
                    _MyDashboardBanner(
                      claims: claims,
                      totalProtected: totalProtected,
                      worker: worker,
                    ),
                    const SizedBox(height: 20),

                    // Active Disruptions — deduplicated by type
                    if (disruptions.isNotEmpty) ...[
                      Row(
                        children: [
                          const Icon(Icons.warning_rounded,
                              color: AppTheme.warning, size: 20),
                          const SizedBox(width: 6),
                          Text(s.activeDisruptions,
                              style: const TextStyle(
                                  fontSize: 16, fontWeight: FontWeight.w700)),
                          const Spacer(),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppTheme.success.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(s.activeDisruptions,
                                style: const TextStyle(
                                    fontSize: 11,
                                    color: AppTheme.success,
                                    fontWeight: FontWeight.w600)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      ...{
                        for (var d in disruptions)
                          (d as Map<String, dynamic>)['disruption_type']: d
                      }
                          .values
                          .toList()
                          .asMap()
                          .entries
                          .map((e) => _DisruptionTile(
                                data: e.value,
                                policyId: policy?['id'] as String?,
                                index: e.key,
                              )),
                      const SizedBox(height: 20),
                    ],

                    // No disruptions
                    if (disruptions.isEmpty) ...[
                      _ClearWeatherCard(city: worker['city'] ?? 'your city'),
                      const SizedBox(height: 20),
                    ],

                    // Simulate button — dev mode only
                    if (ref.watch(devModeProvider)) ...[
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          icon: const Icon(Icons.cloud_rounded,
                              color: AppTheme.warning, size: 18),
                          label: Text(
                            s.simulateEvent,
                            style: const TextStyle(
                                color: AppTheme.warning,
                                fontWeight: FontWeight.w600),
                          ),
                          style: OutlinedButton.styleFrom(
                            side: BorderSide(
                                color: AppTheme.warning.withOpacity(0.5)),
                            backgroundColor:
                                AppTheme.warning.withOpacity(0.06),
                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(14)),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                          onPressed: () => _simulate(
                            context,
                            ref,
                            s,
                            (worker['city'] as String?)?.isNotEmpty == true
                                ? worker['city'] as String
                                : 'Bangalore',
                            (worker['pincode'] as String?)?.isNotEmpty == true
                                ? worker['pincode'] as String
                                : '560001',
                          ),
                        ),
                      ),
                      const SizedBox(height: 4),
                    ],

                    // Recent claims
                    if (claims.isNotEmpty) ...[
                      const SizedBox(height: 24),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(s.claims,
                              style: const TextStyle(
                                  fontSize: 16, fontWeight: FontWeight.w700)),
                          TextButton(
                              onPressed: () => context.go('/claims'),
                              child: Text(s.seeAll)),
                        ],
                      ),
                      ...claims.take(3).map((c) =>
                          _ClaimTile(claim: c as Map<String, dynamic>, s: s)),
                    ],

                    const SizedBox(height: 32),
                  ]),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  void _simulate(BuildContext context, WidgetRef ref, AppStrings s, String city,
      String pincode) async {
    final messenger = ScaffoldMessenger.of(context);
    final api = ref.read(apiServiceProvider);
    try {
      final events = await api.simulateDisruption(city, pincode);
      if (events.isEmpty) {
        messenger.showSnackBar(const SnackBar(
            content: Text('No disruptions detected in your area right now')));
        return;
      }

      // Disruption created — always show green for this
      messenger.showSnackBar(SnackBar(
        content: Text('${events.length} disruption(s) detected in $city!'),
        backgroundColor: AppTheme.success,
        duration: const Duration(seconds: 2),
      ));

      // Refresh dashboard to show the disruption tile
      ref.invalidate(dashboardProvider);

      // Now try to auto-trigger claim
      final eventId = events.first['id'] as String?;
      if (eventId != null) {
        await Future.delayed(const Duration(milliseconds: 800));
        try {
          final claim = await api.triggerClaim(eventId);
          final amount = (claim['approved_amount'] as num?)?.toDouble();
          if (context.mounted) {
            messenger.showSnackBar(SnackBar(
              content: Text(amount == null
                  ? 'Claim submitted for review.'
                  : 'Claim auto-triggered. Payout: Rs.${amount.toStringAsFixed(0)}'),
              backgroundColor: AppTheme.success,
              duration: const Duration(seconds: 4),
            ));
          }
        } catch (claimErr) {
          final errStr = _friendlyClaimError(claimErr, s.noActivePolicy);
          if (context.mounted) {
            messenger.showSnackBar(SnackBar(
              content: Text(errStr),
              backgroundColor: AppTheme.warning,
              duration: const Duration(seconds: 4),
              action: errStr == s.noActivePolicy
                  ? SnackBarAction(
                      label: 'Buy Now',
                      textColor: Colors.white,
                      onPressed: () => context.go('/policy/buy'),
                    )
                  : null,
            ));
          }
        }
      }

      await Future.delayed(const Duration(seconds: 3));
      if (context.mounted) {
        ref.invalidate(dashboardProvider);
        ref.invalidate(claimsProvider);
      }
    } catch (e) {
      messenger.showSnackBar(SnackBar(
          content: Text('Error: $e'), backgroundColor: AppTheme.danger));
    }
  }

  String _friendlyClaimError(Object error, String noActivePolicyText) {
    final text = error.toString();
    if (text.contains('No active policy found')) return noActivePolicyText;
    if (text.contains('Policy has expired')) return 'Your policy has expired. Please renew.';
    if (text.contains('Already claimed')) return 'You already claimed this disruption event.';
    if (text.contains('Weekly payout cap')) return 'Weekly payout cap reached for this policy.';
    if (text.contains('Disruption event is not in your city')) return 'This disruption is not in your city.';
    if (text.contains('not covered')) return 'This disruption type is not covered in your city pool.';
    if (text.contains('Simulation is available only in dev mode')) return 'Simulation is only available in dev mode.';
    if (text.contains('persist for at least')) {
      final match = RegExp(r'at least (\d+) min').firstMatch(text);
      final mins = match?.group(1) ?? '30';
      return 'Disruption must last at least $mins min before claiming.';
    }
    return 'Claim could not be triggered. Please refresh and try again.';
  }

  SliverAppBar _buildAppBar(BuildContext context, String workerName,
      String workerCity, String workerPlatform, dynamic s) {
    return SliverAppBar(
      expandedHeight: 120,
      floating: true,
      backgroundColor: Colors.white,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          padding: const EdgeInsets.fromLTRB(20, 56, 20, 16),
          color: Colors.white,
          child: Row(
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Text(
                    '${s.hello}, $workerName',
                    style: const TextStyle(
                        fontSize: 22, fontWeight: FontWeight.w800),
                  ),
                  Text(
                    '$workerCity • $workerPlatform',
                    style: const TextStyle(
                        color: AppTheme.textSecondary, fontSize: 14),
                  ),
                ],
              ),
              const Spacer(),
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: AppTheme.primaryLight,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Consumer(
                  builder: (context, ref, _) {
                    final notifs =
                        ref.watch(notificationsProvider).valueOrNull ?? [];
                    final unread =
                        notifs.where((n) => n['is_read'] == false).length;
                    return Stack(
                      children: [
                        IconButton(
                          icon: const Icon(Icons.notifications_outlined,
                              color: AppTheme.primary),
                          onPressed: () =>
                              _showNotifications(context, ref, notifs),
                        ),
                        if (unread > 0)
                          Positioned(
                            right: 8,
                            top: 8,
                            child: Container(
                              width: 8,
                              height: 8,
                              decoration: const BoxDecoration(
                                color: AppTheme.danger,
                                shape: BoxShape.circle,
                              ),
                            ),
                          ),
                      ],
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Shield Card with pulse glow when ACTIVE ───────────────────────────────────
class _ShieldCard extends StatefulWidget {
  final Map<String, dynamic>? policy;
  final VoidCallback onTap;
  const _ShieldCard({this.policy, required this.onTap});

  @override
  State<_ShieldCard> createState() => _ShieldCardState();
}

class _ShieldCardState extends State<_ShieldCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _pulse;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1800))
      ..repeat(reverse: true);
    _pulse = Tween<double>(begin: 0.0, end: 10.0)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = ProviderScope.containerOf(context).read(stringsProvider);
    final hasPolicy = widget.policy != null;
    final tier = widget.policy?['tier'] as String? ?? '';
    final tierLabel = AppConstants.tierLabels[tier] ?? s.noPolicyActive;
    final premium =
        (widget.policy?['weekly_premium'] as num?)?.toStringAsFixed(0) ?? '0';
    
    String? endDate;
    try {
      final ed = widget.policy?['end_date'];
      if (ed != null) {
        endDate = DateFormat('dd MMM').format(DateTime.parse(ed.toString()));
      }
    } catch (_) {
      endDate = null;
    }

    return AnimatedBuilder(
      animation: _pulse,
      builder: (_, __) => GestureDetector(
        onTap: widget.onTap,
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: hasPolicy
                  ? [const Color(0xFF1A56DB), const Color(0xFF0EA5E9)]
                  : [const Color(0xFF94A3B8), const Color(0xFF64748B)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
            boxShadow: hasPolicy
                ? [
                    BoxShadow(
                      color: const Color(0xFF1A56DB)
                          .withOpacity(0.25 + _pulse.value * 0.025),
                      blurRadius: 12 + _pulse.value,
                      spreadRadius: _pulse.value * 0.25,
                    )
                  ]
                : null,
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.shield_rounded,
                            color: Colors.white, size: 20),
                        const SizedBox(width: 6),
                        Text(
                          hasPolicy ? tierLabel : s.noActivePolicy,
                          style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w700,
                              fontSize: 16),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    if (hasPolicy) ...[
                      Text('₹$premium/week • Valid till $endDate',
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.85),
                              fontSize: 13)),
                    ] else ...[
                      Text(s.protectionDesc,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.85),
                              fontSize: 13)),
                    ],
                  ],
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  hasPolicy ? s.active.toUpperCase() : s.buyNow.toUpperCase(),
                  style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                      fontSize: 12),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label, value;
  final IconData icon;
  final Color color;
  const _StatCard(
      {required this.label,
      required this.value,
      required this.icon,
      required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.divider, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(height: 10),
          Text(value,
              style:
                  const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
          const SizedBox(height: 2),
          Text(label,
              style:
                  const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
        ],
      ),
    );
  }
}

// ── Disruption Tile with slide-in from left ───────────────────────────────────
class _DisruptionTile extends ConsumerStatefulWidget {
  final Map<String, dynamic> data;
  final String? policyId;
  final int index;
  const _DisruptionTile({required this.data, this.policyId, this.index = 0});

  @override
  ConsumerState<_DisruptionTile> createState() => _DisruptionTileState();
}

class _DisruptionTileState extends ConsumerState<_DisruptionTile>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<Offset> _slide;
  late Animation<double> _fade;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 400));
    _slide = Tween<Offset>(begin: const Offset(-0.4, 0), end: Offset.zero)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));
    _fade = Tween<double>(begin: 0, end: 1)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeIn));
    Future.delayed(Duration(milliseconds: widget.index * 100), () {
      if (mounted) _ctrl.forward();
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final type = widget.data['disruption_type'] as String? ?? '';
    final severity = widget.data['severity'] as String? ?? 'moderate';
    final dss = (widget.data['dss_multiplier'] as num?)?.toDouble() ?? 0.3;
    final label = AppConstants.disruptionLabels[type] ?? type;
    final severityColor =
        Color(AppConstants.severityColors[severity] ?? 0xFFF59E0B);

    return FadeTransition(
      opacity: _fade,
      child: SlideTransition(
        position: _slide,
        child: Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: severityColor.withOpacity(0.3)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: severityColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child:
                    Icon(Icons.warning_rounded, color: severityColor, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(label,
                        style: const TextStyle(
                            fontWeight: FontWeight.w600, fontSize: 14)),
                    Text(
                      '${severity.toUpperCase()} • DSS: ${(dss * 100).toInt()}%',
                      style: const TextStyle(
                          fontSize: 12, color: AppTheme.textSecondary),
                    ),
                  ],
                ),
              ),
              if (widget.policyId != null && false) // removed claim button — auto-triggered
                TextButton(
                  onPressed: () =>
                      _triggerClaim(context, ref, widget.data['id'] as String?),
                  child: const Text('Claim →',
                      style:
                          TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                ),
            ],
          ),
        ),
      ),
    );
  }

  void _triggerClaim(
      BuildContext context, WidgetRef ref, String? eventId) async {
    if (eventId == null) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(apiServiceProvider).triggerClaim(eventId);
      ref.invalidate(dashboardProvider);
      ref.invalidate(claimsProvider);
      await Future.delayed(const Duration(seconds: 2));
      ref.invalidate(dashboardProvider);
      ref.invalidate(claimsProvider);
      messenger.showSnackBar(const SnackBar(
        content: Text('Claim submitted! Check Claims tab.'),
        backgroundColor: Colors.green,
      ));
    } catch (e) {
      messenger.showSnackBar(SnackBar(
          content: Text('Claim failed: $e'), backgroundColor: AppTheme.danger));
    }
  }
}

class _ClearWeatherCard extends StatelessWidget {
  final String city;
  const _ClearWeatherCard({required this.city});

  @override
  Widget build(BuildContext context) {
    final s = ProviderScope.containerOf(context).read(stringsProvider);
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.success.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.check_circle_rounded,
              color: AppTheme.success, size: 28),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(s.allClear,
                  style: const TextStyle(
                      fontWeight: FontWeight.w700, fontSize: 15)),
              Text('${s.noDisruptions} in $city',
                  style: const TextStyle(
                      color: AppTheme.textSecondary, fontSize: 13)),
            ],
          ),
        ],
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;
  const _QuickAction(
      {required this.icon,
      required this.label,
      required this.color,
      required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 22),
            const SizedBox(width: 8),
            Expanded(
                child: Text(label,
                    style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 13,
                        color: color))),
          ],
        ),
      ),
    );
  }
}

class _ClaimTile extends StatelessWidget {
  final Map<String, dynamic> claim;
  final dynamic s;
  const _ClaimTile({required this.claim, required this.s});

  @override
  Widget build(BuildContext context) {
    final status = claim['status'] as String? ?? 'pending';
    final amount = (claim['approved_amount'] as num?)?.toDouble() ??
        (claim['claimed_amount'] as num?)?.toDouble() ??
        0;
    final date = claim['created_at'] != null
        ? DateFormat('dd MMM')
            .format(DateTime.parse(claim['created_at'] as String))
        : '';
    final statusColor = {
          'paid': AppTheme.success,
          'approved': AppTheme.primary,
          'rejected': AppTheme.danger,
          'pending': AppTheme.warning,
        }[status] ??
        AppTheme.textSecondary;
    final statusLabel = {
          'paid': s.paid,
          'approved': s.approved,
          'pending': s.pending,
        }[status] ??
        status.toUpperCase();

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.divider, width: 0.5),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Claim • $date',
                    style: const TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 14)),
                Text('₹${amount.toStringAsFixed(0)}',
                    style: const TextStyle(
                        color: AppTheme.textSecondary, fontSize: 13)),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(statusLabel,
                style: TextStyle(
                    color: statusColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
  }
}

// ── My Dashboard Banner ───────────────────────────────────────────────────────
class _MyDashboardBanner extends StatelessWidget {
  final List<dynamic> claims;
  final double totalProtected;
  final Map<String, dynamic> worker;
  const _MyDashboardBanner({
    required this.claims,
    required this.totalProtected,
    required this.worker,
  });

  @override
  Widget build(BuildContext context) {
    final paid = claims.where((c) => (c as Map)['status'] == 'paid').length;
    final pending = claims.where((c) => (c as Map)['status'] == 'pending').length;

    return GestureDetector(
      onTap: () => _showPersonalDashboard(context, claims, totalProtected, worker),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF0F172A), Color(0xFF1E3A5F)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.bar_chart_rounded, color: Colors.white, size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('My Protection Dashboard',
                      style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                          fontSize: 14)),
                  const SizedBox(height: 3),
                  Text(
                    '${claims.length} claims • ₹${totalProtected.toStringAsFixed(0)} earned • $paid paid',
                    style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 12),
                  ),
                ],
              ),
            ),
            if (pending > 0)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.warning.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text('$pending pending',
                    style: const TextStyle(
                        color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
              ),
            const SizedBox(width: 8),
            const Icon(Icons.chevron_right_rounded, color: Colors.white54, size: 20),
          ],
        ),
      ),
    );
  }
}

void _showPersonalDashboard(
  BuildContext context,
  List<dynamic> claims,
  double totalProtected,
  Map<String, dynamic> worker,
) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => _PersonalDashboardSheet(
      claims: claims,
      totalProtected: totalProtected,
      worker: worker,
    ),
  );
}

class _PersonalDashboardSheet extends StatelessWidget {
  final List<dynamic> claims;
  final double totalProtected;
  final Map<String, dynamic> worker;
  const _PersonalDashboardSheet({
    required this.claims,
    required this.totalProtected,
    required this.worker,
  });

  @override
  Widget build(BuildContext context) {
    final paidAmount = claims
        .where((c) => (c as Map)['status'] == 'paid')
        .fold(0.0, (sum, c) => sum + ((c as Map)['approved_amount'] as num? ?? 0).toDouble());
    final pending = claims.where((c) => (c as Map)['status'] == 'pending').length;
    final rejected = claims.where((c) => (c as Map)['status'] == 'rejected').length;

    return DraggableScrollableSheet(
      initialChildSize: 0.85,
      maxChildSize: 0.95,
      minChildSize: 0.5,
      builder: (_, ctrl) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          children: [
            Container(
              margin: const EdgeInsets.only(top: 12),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppTheme.divider,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: Row(
                children: [
                  const Icon(Icons.bar_chart_rounded, color: AppTheme.primary, size: 22),
                  const SizedBox(width: 10),
                  const Text('My Protection Dashboard',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close_rounded, size: 20),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: ListView(
                controller: ctrl,
                padding: const EdgeInsets.all(20),
                children: [
                  // Summary stats
                  Row(
                    children: [
                      _DashStat('Total Earned', '₹${totalProtected.toStringAsFixed(0)}',
                          Icons.savings_rounded, AppTheme.success),
                      const SizedBox(width: 12),
                      _DashStat('Claims Filed', '${claims.length}',
                          Icons.receipt_long_rounded, AppTheme.primary),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      _DashStat('Paid Out', '₹${paidAmount.toStringAsFixed(0)}',
                          Icons.payments_rounded, AppTheme.success),
                      const SizedBox(width: 12),
                      _DashStat('Pending / Rejected', '$pending / $rejected',
                          Icons.pending_rounded, AppTheme.warning),
                    ],
                  ),
                  const SizedBox(height: 24),
                  const Text('Claim History',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 12),
                  if (claims.isEmpty)
                    Center(
                      child: Padding(
                        padding: const EdgeInsets.all(32),
                        child: Column(
                          children: [
                            Icon(Icons.receipt_long_outlined,
                                size: 48, color: AppTheme.textHint),
                            const SizedBox(height: 12),
                            const Text('No claims yet',
                                style: TextStyle(
                                    color: AppTheme.textSecondary, fontSize: 15)),
                          ],
                        ),
                      ),
                    )
                  else
                    ...claims.map((c) =>
                        _ClaimDetailCard(claim: c as Map<String, dynamic>)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DashStat extends StatelessWidget {
  final String label, value;
  final IconData icon;
  final Color color;
  const _DashStat(this.label, this.value, this.icon, this.color);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 8),
            Text(value,
                style: TextStyle(
                    fontSize: 20, fontWeight: FontWeight.w800, color: color)),
            Text(label,
                style: const TextStyle(
                    fontSize: 11,
                    color: AppTheme.textSecondary,
                    fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}

class _ClaimDetailCard extends StatelessWidget {
  final Map<String, dynamic> claim;
  const _ClaimDetailCard({required this.claim});

  @override
  Widget build(BuildContext context) {
    final status = claim['status'] as String? ?? 'pending';
    final approved = (claim['approved_amount'] as num?)?.toDouble();
    final claimed = (claim['claimed_amount'] as num?)?.toDouble() ?? 0;
    final dss = ((claim['dss_multiplier'] as num?)?.toDouble() ?? 0) * 100;
    final hoursRatio = ((claim['active_hours_ratio'] as num?)?.toDouble() ?? 0) * 100;
    final fraudScore = (claim['fraud_score'] as num?)?.toDouble() ?? 0;
    final autoApproved = claim['auto_approved'] as bool? ?? false;

    String dateStr = '', timeStr = '', dayStr = '';
    if (claim['created_at'] != null) {
      final dt = DateTime.parse(claim['created_at'] as String).toLocal();
      dateStr = DateFormat('dd MMM yyyy').format(dt);
      timeStr = DateFormat('hh:mm a').format(dt);
      dayStr = DateFormat('EEEE').format(dt);
    }

    final statusColor = {
      'paid': AppTheme.success,
      'approved': AppTheme.primary,
      'rejected': AppTheme.danger,
      'pending': AppTheme.warning,
    }[status] ?? AppTheme.textSecondary;

    final disruptionType = (claim['disruption_type'] as String? ?? '')
        .replaceAll('_', ' ')
        .split(' ')
        .map((w) => w.isNotEmpty ? '${w[0].toUpperCase()}${w.substring(1)}' : '')
        .join(' ');

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: statusColor.withOpacity(0.3), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: statusColor.withOpacity(0.06),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                // Date block
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppTheme.surface,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    children: [
                      Text(
                        dateStr.isNotEmpty ? dateStr.split(' ')[0] : '--',
                        style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                            color: statusColor),
                      ),
                      Text(
                        dateStr.isNotEmpty
                            ? '${dateStr.split(' ')[1]} ${dateStr.split(' ')[2]}'
                            : '',
                        style: const TextStyle(
                            fontSize: 10, color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        disruptionType.isNotEmpty ? disruptionType : 'Disruption Event',
                        style: const TextStyle(
                            fontWeight: FontWeight.w700, fontSize: 14),
                      ),
                      const SizedBox(height: 2),
                      Text('$dayStr • $timeStr',
                          style: const TextStyle(
                              fontSize: 12, color: AppTheme.textSecondary)),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          if (autoApproved)
                            Container(
                              margin: const EdgeInsets.only(right: 6),
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryLight,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text('AI AUTO',
                                  style: TextStyle(
                                      fontSize: 9,
                                      color: AppTheme.primary,
                                      fontWeight: FontWeight.w700)),
                            ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: statusColor.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(status.toUpperCase(),
                                style: TextStyle(
                                    fontSize: 9,
                                    color: statusColor,
                                    fontWeight: FontWeight.w700)),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '₹${(approved ?? claimed).toStringAsFixed(0)}',
                      style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          color: statusColor),
                    ),
                    if (approved != null && approved != claimed)
                      Text(
                        'of ₹${claimed.toStringAsFixed(0)}',
                        style: const TextStyle(
                            fontSize: 10, color: AppTheme.textSecondary),
                      ),
                  ],
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: const BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(16),
                bottomRight: Radius.circular(16),
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _MiniStat('Disruption', '${dss.toInt()}%'),
                _MiniStat('Hours Affected', '${hoursRatio.toInt()}%'),
                _MiniStat(
                  'Risk Score',
                  '${(fraudScore * 100).toInt()}',
                  color: fraudScore > 0.7
                      ? AppTheme.danger
                      : fraudScore > 0.3
                          ? AppTheme.warning
                          : AppTheme.success,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  final String label, value;
  final Color? color;
  const _MiniStat(this.label, this.value, {this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value,
            style: TextStyle(
                fontWeight: FontWeight.w700,
                fontSize: 13,
                color: color ?? AppTheme.textPrimary)),
        const SizedBox(height: 2),
        Text(label,
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 10)),
      ],
    );
  }
}
