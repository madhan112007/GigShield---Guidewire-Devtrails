import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:razorpay_flutter/razorpay_flutter.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/utils/constants.dart';

class BuyPolicyScreen extends ConsumerStatefulWidget {
  const BuyPolicyScreen({super.key});

  @override
  ConsumerState<BuyPolicyScreen> createState() => _BuyPolicyScreenState();
}

class _BuyPolicyScreenState extends ConsumerState<BuyPolicyScreen> {
  bool _purchasing = false;
  late Razorpay _razorpay;
  Map<String, dynamic>? _pendingOrder;

  @override
  void initState() {
    super.initState();
    _razorpay = Razorpay();
    _razorpay.on(Razorpay.EVENT_PAYMENT_SUCCESS, _onPaymentSuccess);
    _razorpay.on(Razorpay.EVENT_PAYMENT_ERROR, _onPaymentError);
    _razorpay.on(Razorpay.EVENT_EXTERNAL_WALLET, _onExternalWallet);
  }

  @override
  void dispose() {
    _razorpay.clear();
    super.dispose();
  }

  void _buy(String tier) async {
    setState(() => _purchasing = true);
    try {
      if (ref.read(devModeProvider)) {
        await ref.read(apiServiceProvider).createPolicy(tier);
        ref.invalidate(activePolicyProvider);
        ref.invalidate(dashboardProvider);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
                content: Text('Demo policy activated.'),
                backgroundColor: AppTheme.success),
          );
          context.go('/policy');
        }
        return;
      }

      final order = await ref.read(apiServiceProvider).createPolicyOrder(tier);
      _pendingOrder = {'order': order, 'tier': tier};

      _razorpay.open({
        'key': order['key_id'],
        'order_id': order['order_id'],
        'amount': order['amount'],
        'currency': 'INR',
        'name': 'Susanoo',
        'description':
            '${AppConstants.tierLabels[tier] ?? tier} — Weekly Policy',
        'prefill': {'contact': '', 'email': 'worker@susanoo.in'},
        'theme': {'color': '#1A56DB'},
        'modal': {'confirm_close': true},
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Error: $e'), backgroundColor: AppTheme.danger),
        );
      }
    } finally {
      if (mounted) setState(() => _purchasing = false);
    }
  }

  void _onPaymentSuccess(PaymentSuccessResponse response) async {
    final order = _pendingOrder?['order'] as Map<String, dynamic>?;
    final tier = _pendingOrder?['tier'] as String?;
    if (order == null || tier == null) return;
    try {
      await ref.read(apiServiceProvider).verifyPolicyPayment({
        'razorpay_order_id': response.orderId,
        'razorpay_payment_id': response.paymentId,
        'razorpay_signature': response.signature,
        'tier': tier,
      });
      ref.invalidate(activePolicyProvider);
      ref.invalidate(dashboardProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('🎉 Payment successful! Policy activated.'),
            backgroundColor: AppTheme.success,
          ),
        );
        context.go('/policy');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Verification failed: $e'),
              backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  void _onPaymentError(PaymentFailureResponse response) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Payment failed: ${response.message}'),
          backgroundColor: AppTheme.danger,
        ),
      );
    }
  }

  void _onExternalWallet(ExternalWalletResponse response) {}

  @override
  Widget build(BuildContext context) {
    final selectedTier = ref.watch(selectedTierProvider);
    final quoteAsync = ref.watch(premiumQuoteProvider(selectedTier));

    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(
        title: const Text('Choose Your Shield'),
        backgroundColor: Colors.white,
        leading: BackButton(onPressed: () => context.pop()),
      ),
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Weekly income protection\nstarting from ₹29/week',
                    style: TextStyle(
                        fontSize: 20, fontWeight: FontWeight.w700, height: 1.3),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Cancel anytime. Coverage renews every 7 days.',
                    style:
                        TextStyle(color: AppTheme.textSecondary, fontSize: 14),
                  ),
                  const SizedBox(height: 24),
                  ..._tiers.map((t) => _TierCard(
                        tier: t,
                        selected: selectedTier == t['value'],
                        onSelect: () => ref
                            .read(selectedTierProvider.notifier)
                            .state = t['value']!,
                      )),
                  const SizedBox(height: 24),
                  quoteAsync.when(
                    loading: () =>
                        const Center(child: CircularProgressIndicator()),
                    error: (_, __) => const SizedBox.shrink(),
                    data: (quote) => _QuoteBreakdown(quote: quote),
                  ),
                ],
              ),
            ),
          ),

          // Bottom CTA
          Container(
            padding: const EdgeInsets.all(20),
            decoration: const BoxDecoration(
              color: Colors.white,
              border:
                  Border(top: BorderSide(color: AppTheme.divider, width: 0.5)),
            ),
            child: quoteAsync.when(
              loading: () => const SizedBox(height: 56),
              error: (_, __) => const SizedBox.shrink(),
              data: (quote) => ElevatedButton(
                onPressed: _purchasing ? null : () => _buy(selectedTier),
                child: _purchasing
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2))
                    : Text(
                        'Pay ₹${(quote['adjusted_premium'] as num).toStringAsFixed(0)} via Razorpay'),
              ),
            ),
          ),
        ],
      ),
    );
  }

  static const List<Map<String, String>> _tiers = [
    {
      'value': 'basic',
      'label': '🥉 Basic Shield',
      'price': '₹29',
      'payout': 'Up to ₹300/day',
      'triggers': 'Rain only',
      'desc': 'Essential rain cover for monsoon months',
    },
    {
      'value': 'smart',
      'label': '🥈 Smart Shield',
      'price': '₹49',
      'payout': 'Up to ₹550/day',
      'triggers': 'Rain + Heat + AQI',
      'desc': 'Best value. Covers the 3 most common disruptions',
      'popular': 'true',
    },
    {
      'value': 'pro',
      'label': '🥇 Pro Shield',
      'price': '₹79',
      'payout': 'Up to ₹750/day',
      'triggers': 'All 5 triggers',
      'desc': 'Maximum protection including traffic & emergencies',
    },
  ];
}

class _TierCard extends StatelessWidget {
  final Map<String, String> tier;
  final bool selected;
  final VoidCallback onSelect;
  const _TierCard(
      {required this.tier, required this.selected, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    final isPopular = tier['popular'] == 'true';
    return GestureDetector(
      onTap: onSelect,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: selected ? AppTheme.primaryLight : Colors.white,
          border: Border.all(
            color: selected ? AppTheme.primary : AppTheme.divider,
            width: selected ? 2 : 0.5,
          ),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(tier['label']!,
                    style: const TextStyle(
                        fontWeight: FontWeight.w700, fontSize: 16)),
                const Spacer(),
                if (isPopular)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                        color: AppTheme.primary,
                        borderRadius: BorderRadius.circular(6)),
                    child: const Text('POPULAR',
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w700)),
                  ),
                const SizedBox(width: 8),
                Text(tier['price']!,
                    style: const TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 20,
                        color: AppTheme.primary)),
                const Text('/wk',
                    style:
                        TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
              ],
            ),
            const SizedBox(height: 6),
            Text(tier['desc']!,
                style: const TextStyle(
                    color: AppTheme.textSecondary, fontSize: 13)),
            const SizedBox(height: 10),
            Row(
              children: [
                _Pill(text: tier['payout']!, color: AppTheme.success),
                const SizedBox(width: 8),
                _Pill(text: tier['triggers']!, color: AppTheme.primary),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  final String text;
  final Color color;
  const _Pill({required this.text, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(text,
          style: TextStyle(
              color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}

class _QuoteBreakdown extends StatelessWidget {
  final Map<String, dynamic> quote;
  const _QuoteBreakdown({required this.quote});

  @override
  Widget build(BuildContext context) {
    final base = (quote['base_premium'] as num).toStringAsFixed(0);
    final adjusted = (quote['adjusted_premium'] as num).toStringAsFixed(2);
    final zone = (quote['zone_risk_multiplier'] as num).toStringAsFixed(2);
    final season = (quote['season_factor'] as num).toStringAsFixed(2);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.divider, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.auto_awesome, color: AppTheme.primary, size: 16),
              SizedBox(width: 6),
              Text('AI-Adjusted Premium',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 12),
          _Row('Base premium', '₹$base'),
          _Row('Zone risk factor', '×$zone'),
          _Row('Season factor', '×$season'),
          const Divider(),
          _Row('Your weekly premium', '₹$adjusted', bold: true),
        ],
      ),
    );
  }

  Widget _Row(String label, String val, {bool bold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: TextStyle(
                  color: bold ? AppTheme.textPrimary : AppTheme.textSecondary,
                  fontSize: 13)),
          Text(val,
              style: TextStyle(
                  fontWeight: bold ? FontWeight.w800 : FontWeight.w500,
                  fontSize: 13,
                  color: bold ? AppTheme.primary : AppTheme.textPrimary)),
        ],
      ),
    );
  }
}
