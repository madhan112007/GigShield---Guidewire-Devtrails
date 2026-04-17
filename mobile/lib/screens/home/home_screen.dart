import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:susanoo/providers/locale_provider.dart';
import 'package:susanoo/l10n/app_strings.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/utils/constants.dart';

void _showNotifications(BuildContext context, WidgetRef ref, List<dynamic> notifs) {
  showModalBottomSheet(
    context: context,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
    builder: (_) => Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
          child: Row(
            children: [
              const Text('Notifications', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
              const Spacer(),
              if (notifs.any((n) => n['is_read'] == false))
                TextButton(
                  onPressed: () async {
                    await ref.read(apiServiceProvider).markAllNotificationsRead();
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
              ? const Center(child: Text('No notifications yet', style: TextStyle(color: Colors.grey)))
              : ListView.separated(
                  itemCount: notifs.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (_, i) {
                    final n = notifs[i] as Map<String, dynamic>;
                    final isRead = n['is_read'] == true;
                    return ListTile(
                      leading: CircleAvatar(
                        backgroundColor: isRead ? Colors.grey.shade100 : AppTheme.primaryLight,
                        child: Icon(
                          _notifIcon(n['notif_type'] as String? ?? ''),
                          color: isRead ? Colors.grey : AppTheme.primary,
                          size: 18,
                        ),
                      ),
                      title: Text(n['title'] ?? '', style: TextStyle(fontWeight: isRead ? FontWeight.w400 : FontWeight.w700, fontSize: 14)),
                      subtitle: Text(n['body'] ?? '', style: const TextStyle(fontSize: 12)),
                      tileColor: isRead ? null : AppTheme.primaryLight.withOpacity(0.3),
                      onTap: () async {
                        await ref.read(apiServiceProvider).markNotificationRead(n['id'] as String);
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
    case 'claim_approved': return Icons.thumb_up_rounded;
    case 'claim_paid': return Icons.payments_rounded;
    case 'claim_rejected': return Icons.cancel_rounded;
    case 'disruption_detected': return Icons.warning_rounded;
    case 'policy_expiring': return Icons.timer_rounded;
    default: return Icons.notifications_rounded;
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
          final disruptions = data['active_disruptions'] as List<dynamic>? ?? [];
          final claims = data['recent_claims'] as List<dynamic>? ?? [];
          final totalProtected = (data['total_earned_protection'] as num?)?.toDouble() ?? 0.0;

          return CustomScrollView(
            slivers: [
              _buildAppBar(context, worker, s),
              SliverPadding(
                padding: const EdgeInsets.all(20),
                sliver: SliverList(
                  delegate: SliverChildListDelegate([
                    // Shield status card
                    _ShieldCard(policy: policy, onTap: () => context.go('/policy')),
                    const SizedBox(height: 16),

                    // Stats row
                    Row(
                      children: [
                        Expanded(child: _StatCard(
                          label: s.policy,
                          value: '₹${totalProtected.toStringAsFixed(0)}',
                          icon: Icons.savings_rounded,
                          color: AppTheme.success,
                        )),
                        const SizedBox(width: 12),
                        Expanded(child: _StatCard(
                          label: s.claims,
                          value: '${claims.length}',
                          icon: Icons.receipt_long_rounded,
                          color: AppTheme.primary,
                        )),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Active Disruptions — deduplicated by type
                    if (disruptions.isNotEmpty) ...[
                      Row(
                        children: [
                          const Icon(Icons.warning_rounded, color: AppTheme.warning, size: 20),
                          const SizedBox(width: 6),
                          Text(s.activeDisruptions, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                          const Spacer(),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppTheme.success.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(s.activeDisruptions, style: const TextStyle(fontSize: 11, color: AppTheme.success, fontWeight: FontWeight.w600)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      ...{ for (var d in disruptions) (d as Map<String, dynamic>)['disruption_type']: d }.values
                          .toList()
                          .asMap()
                          .entries
                          .map((e) => _DisruptionTile(data: e.value as Map<String, dynamic>, policyId: null, index: e.key)),
                      const SizedBox(height: 20),
                    ],

                    // No disruptions
                    if (disruptions.isEmpty) ...[
                      _ClearWeatherCard(city: worker['city'] ?? 'your city'),
                      const SizedBox(height: 20),
                    ],

                    // Quick actions
                    Text(s.quickActions, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Expanded(child: _QuickAction(
                          icon: Icons.add_circle_rounded,
                          label: policy == null ? s.buyPolicy : s.buyPolicy,
                          color: AppTheme.primary,
                          onTap: () => context.go('/policy/buy'),
                        )),
                        if (ref.watch(devModeProvider)) ...[
                          const SizedBox(width: 12),
                          Expanded(child: _QuickAction(
                            icon: Icons.cloud_rounded,
                            label: s.simulateEvent,
                            color: AppTheme.warning,
                            onTap: () => _simulate(
                context, ref, s,
                (worker['city'] as String?)?.isNotEmpty == true ? worker['city'] as String : 'Bangalore',
                (worker['pincode'] as String?)?.isNotEmpty == true ? worker['pincode'] as String : '560001',
              ),
                          )),
                        ],
                      ],
                    ),

                    // Recent claims
                    if (claims.isNotEmpty) ...[
                      const SizedBox(height: 24),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(s.claims, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                          TextButton(onPressed: () => context.go('/claims'), child: Text(s.seeAll)),
                        ],
                      ),
                      ...claims.take(3).map((c) => _ClaimTile(claim: c as Map<String, dynamic>, s: s)),
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

  void _simulate(BuildContext context, WidgetRef ref, AppStrings s, String city, String pincode) async {
    final messenger = ScaffoldMessenger.of(context);
    final api = ref.read(apiServiceProvider);
    try {
      final events = await api.simulateDisruption(city, pincode);
      if (events.isEmpty) {
        messenger.showSnackBar(const SnackBar(content: Text('No disruptions detected in your area right now')));
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
          await api.triggerClaim(eventId);
          if (context.mounted) {
            messenger.showSnackBar(SnackBar(
              content: Text('Claim auto-triggered! ₹ payout initiated.'),
              backgroundColor: AppTheme.success,
              duration: const Duration(seconds: 4),
            ));
          }
        } catch (claimErr) {
          final errStr = claimErr.toString();
          if (context.mounted) {
            String message = s.noActivePolicy;
            if (errStr.contains('Policy has expired')) message = s.policyExpiring;
            if (errStr.contains('not in your city')) message = s.notInYourCity;
            if (errStr.contains('not covered in')) message = s.notCoveredInPool;
            if (errStr.contains('Already claimed')) message = s.alreadyClaimed;
            if (errStr.contains('Weekly payout cap')) message = s.capReached;

            messenger.showSnackBar(SnackBar(
              content: Text(message),
              backgroundColor: AppTheme.warning,
              duration: const Duration(seconds: 4),
              action: message == s.noActivePolicy ? SnackBarAction(
                label: 'Buy Now',
                textColor: Colors.white,
                onPressed: () => context.go('/policy/buy'),
              ) : null,
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
      messenger.showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.danger));
    }
  }

  SliverAppBar _buildAppBar(BuildContext context, Map<String, dynamic> worker, dynamic s) {
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
                    '${s.hello}, ${(worker['name'] as String?)?.split(' ').first ?? 'Rider'}',
                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
                  ),
                  Text(
                    '${worker['city'] ?? ''} • ${(worker['platform'] as String?)?.toUpperCase() ?? ''}',
                    style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14),
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
                    final notifs = ref.watch(notificationsProvider).valueOrNull ?? [];
                    final unread = notifs.where((n) => n['is_read'] == false).length;
                    return Stack(
                      children: [
                        IconButton(
                          icon: const Icon(Icons.notifications_outlined, color: AppTheme.primary),
                          onPressed: () => _showNotifications(context, ref, notifs),
                        ),
                        if (unread > 0)
                          Positioned(
                            right: 8, top: 8,
                            child: Container(
                              width: 8, height: 8,
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

class _ShieldCardState extends State<_ShieldCard> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _pulse;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1800))
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
    final premium = (widget.policy?['weekly_premium'] as num?)?.toStringAsFixed(0) ?? '0';
    final endDate = widget.policy?['end_date'] != null
        ? DateFormat('dd MMM').format(DateTime.parse(widget.policy!['end_date']))
        : null;

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
                ? [BoxShadow(
                    color: const Color(0xFF1A56DB).withOpacity(0.25 + _pulse.value * 0.025),
                    blurRadius: 12 + _pulse.value,
                    spreadRadius: _pulse.value * 0.25,
                  )]
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
                        const Icon(Icons.shield_rounded, color: Colors.white, size: 20),
                        const SizedBox(width: 6),
                        Text(
                          hasPolicy ? tierLabel : s.noActivePolicy,
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    if (hasPolicy) ...[
                      Text('₹$premium/week • Valid till $endDate',
                          style: TextStyle(color: Colors.white.withOpacity(0.85), fontSize: 13)),
                    ] else ...[
                      Text(s.protectionDesc,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(color: Colors.white.withOpacity(0.85), fontSize: 13)),
                    ],
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  hasPolicy ? s.active.toUpperCase() : s.buyNow.toUpperCase(),
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 12),
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
  const _StatCard({required this.label, required this.value, required this.icon, required this.color});

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
          Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
          const SizedBox(height: 2),
          Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
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
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 400));
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
    final severityColor = Color(AppConstants.severityColors[severity] ?? 0xFFF59E0B);

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
                child: Icon(Icons.warning_rounded, color: severityColor, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                    Text(
                      '${severity.toUpperCase()} • DSS: ${(dss * 100).toInt()}%',
                      style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                    ),
                  ],
                ),
              ),
              if (widget.policyId != null)
                TextButton(
                  onPressed: () => _triggerClaim(context, ref, widget.data['id'] as String?),
                  child: const Text('Claim →', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                ),
            ],
          ),
        ),
      ),
    );
  }

  void _triggerClaim(BuildContext context, WidgetRef ref, String? eventId) async {
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
      messenger.showSnackBar(SnackBar(content: Text('Claim failed: $e'), backgroundColor: AppTheme.danger));
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
          const Icon(Icons.check_circle_rounded, color: AppTheme.success, size: 28),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(s.allClear, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
              Text('${s.noDisruptions} in $city', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
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
  const _QuickAction({required this.icon, required this.label, required this.color, required this.onTap});

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
            Expanded(child: Text(label, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: color))),
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
    final amount = (claim['approved_amount'] as num?)?.toDouble() ?? (claim['claimed_amount'] as num?)?.toDouble() ?? 0;
    final date = claim['created_at'] != null
        ? DateFormat('dd MMM').format(DateTime.parse(claim['created_at'] as String))
        : '';
    final statusColor = {
      'paid': AppTheme.success,
      'approved': AppTheme.primary,
      'rejected': AppTheme.danger,
      'pending': AppTheme.warning,
    }[status] ?? AppTheme.textSecondary;
    final statusLabel = {
      'paid': s.paid,
      'approved': s.approved,
      'pending': s.pending,
    }[status] ?? status.toUpperCase();

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
                Text('Claim • $date', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                Text('₹${amount.toStringAsFixed(0)}', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(statusLabel, style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
  }
}
