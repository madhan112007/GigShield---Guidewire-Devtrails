import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/providers/locale_provider.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/utils/constants.dart';
import 'package:susanoo/l10n/app_strings.dart';

class TermsScreen extends ConsumerStatefulWidget {
  const TermsScreen({super.key});

  @override
  ConsumerState<TermsScreen> createState() => _TermsScreenState();
}

class _TermsScreenState extends ConsumerState<TermsScreen> {
  bool _acceptedTerms = false;
  bool _acceptedPrivacy = false;
  bool _acceptedDataConsent = false;
  final _scrollCtrl = ScrollController();
  bool _hasScrolledToBottom = false;

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(() {
      if (_scrollCtrl.position.pixels >=
          _scrollCtrl.position.maxScrollExtent - 80) {
        if (!_hasScrolledToBottom) setState(() => _hasScrolledToBottom = true);
      }
    });
  }

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _accept() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(AppConstants.termsAcceptedKey, true);
    if (!mounted) return;
    final loggedIn = await ref.read(apiServiceProvider).isLoggedIn();
    if (!mounted) return;
    context.go(loggedIn ? '/home' : '/auth/phone');
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final currentLang = ref.watch(localeProvider);
    final allAccepted = _acceptedTerms && _acceptedPrivacy && _acceptedDataConsent;

    return Scaffold(
      backgroundColor: AppTheme.surface,
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
              color: Colors.white,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Language picker
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: AppStrings.all.entries.map((entry) {
                      final isSelected = entry.key == currentLang;
                      return GestureDetector(
                        onTap: () => ref.read(localeProvider.notifier).setLanguage(entry.key),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          margin: const EdgeInsets.only(left: 6),
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: isSelected ? AppTheme.primary : AppTheme.surface,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: isSelected ? AppTheme.primary : AppTheme.divider,
                            ),
                          ),
                          child: Text(
                            entry.value.languageName,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: isSelected ? FontWeight.w700 : FontWeight.w400,
                              color: isSelected ? Colors.white : AppTheme.textSecondary,
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryLight,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.shield_rounded, color: AppTheme.primary, size: 28),
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Susanoo',
                              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                          Text(s.termsAndConditions,
                              style: TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFF8E1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFFFFE082)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.info_outline_rounded, size: 14, color: Color(0xFFF59E0B)),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            s.pleaseReadTerms,
                            style: TextStyle(fontSize: 12, color: Colors.brown.shade700),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const Divider(height: 1, color: AppTheme.divider),

            // Scrollable content
            Expanded(
              child: ListView(
                controller: _scrollCtrl,
                padding: const EdgeInsets.all(20),
                children: [
                  _SectionCard(
                    icon: Icons.gavel_rounded,
                    title: '1. Terms of Service',
                    color: AppTheme.primary,
                    content: [
                      _Clause('1.1 Acceptance', 'By using Susanoo, you agree to be bound by these Terms of Service. If you do not agree, you may not access or use the platform.'),
                      _Clause('1.2 Eligibility', 'You must be at least 18 years of age and an active gig delivery worker registered on a supported platform (Blinkit, Zepto, Swiggy Instamart, Zomato, Amazon, or BigBasket) to use this service.'),
                      _Clause('1.3 Account Responsibility', 'You are responsible for maintaining the confidentiality of your account credentials. You agree to notify us immediately of any unauthorized use of your account.'),
                      _Clause('1.4 Prohibited Use', 'You may not use Susanoo for any unlawful purpose, to submit fraudulent claims, to impersonate another person, or to interfere with the platform\'s operation.'),
                      _Clause('1.5 Modifications', 'Susanoo reserves the right to modify these terms at any time. Continued use of the platform after changes constitutes acceptance of the revised terms.'),
                    ],
                  ),
                  const SizedBox(height: 16),

                  _SectionCard(
                    icon: Icons.verified_user_rounded,
                    title: '2. Insurance Policy Terms',
                    color: AppTheme.success,
                    content: [
                      _Clause('2.1 Parametric Insurance', 'Susanoo provides parametric income protection insurance. Claims are triggered automatically based on verified disruption events (weather, AQI, civic emergencies) — not on actual income loss documentation.'),
                      _Clause('2.2 Coverage Scope', 'Coverage is limited to active policy periods and disruption events occurring within your registered delivery city and pincode. Events outside your zone are not covered.'),
                      _Clause('2.3 Payout Calculation', 'Payouts are calculated using your average daily earnings multiplied by the Disruption Severity Score (DSS) and your active hours ratio. The DSS is determined by real-time data from verified sources.'),
                      _Clause('2.4 Claim Limits', 'Maximum daily and weekly payout limits apply based on your selected policy tier (Basic, Smart, or Pro). Claims exceeding these limits will be capped at the tier maximum.'),
                      _Clause('2.5 Fraud Prevention', 'All claims are subject to automated fraud scoring. Claims flagged as suspicious may be held for manual review. GPS spoofing or false location data will result in claim rejection and account suspension.'),
                      _Clause('2.6 No-Claim Guarantee', 'Premiums paid are non-refundable. If no qualifying disruption events occur during your policy period, no payout will be made. This is the nature of parametric insurance.'),
                    ],
                  ),
                  const SizedBox(height: 16),

                  _SectionCard(
                    icon: Icons.lock_rounded,
                    title: '3. Privacy Policy',
                    color: const Color(0xFF7C3AED),
                    content: [
                      _Clause('3.1 Data We Collect', 'We collect your mobile number, name, city, pincode, UPI ID, platform worker ID, GPS location pings (every 10 minutes during active hours), and device information.'),
                      _Clause('3.2 Purpose of Collection', 'Your data is used solely for: (a) identity verification, (b) disruption zone matching, (c) fraud detection via GPS movement analysis, (d) payout processing via UPI, and (e) improving our risk models.'),
                      _Clause('3.3 Data Sharing', 'We do not sell your personal data. We share data only with: payment processors (Razorpay) for UPI payouts, weather/AQI data providers for disruption verification, and regulatory authorities when legally required.'),
                      _Clause('3.4 Data Retention', 'Your data is retained for the duration of your account plus 7 years for regulatory compliance. Location pings are retained for 90 days for fraud analysis.'),
                      _Clause('3.5 Your Rights', 'You have the right to access, correct, or delete your personal data. To exercise these rights, contact support. Note that deletion of certain data may affect your ability to file claims.'),
                      _Clause('3.6 Security', 'We use industry-standard encryption (TLS 1.3) for data in transit and AES-256 for data at rest. Access tokens are stored in secure device storage.'),
                    ],
                  ),
                  const SizedBox(height: 16),

                  _SectionCard(
                    icon: Icons.location_on_rounded,
                    title: '4. Location & Data Consent',
                    color: AppTheme.warning,
                    content: [
                      _Clause('4.1 Location Access', 'Susanoo requires access to your device\'s GPS location to: (a) verify you are within an active disruption zone, (b) detect GPS spoofing attempts, and (c) improve hyper-local risk models.'),
                      _Clause('4.2 Background Location', 'Location is collected only during active hours (6 AM – 10 PM) at 10-minute intervals. We do not collect location data outside these hours or when the app is closed.'),
                      _Clause('4.3 Consent Withdrawal', 'You may revoke location access at any time via device settings. However, revoking location access will disable automatic claim triggering and may affect claim eligibility.'),
                      _Clause('4.4 Data Processing', 'By accepting, you consent to the processing of your personal data as described in this agreement, including cross-border data transfers to our cloud infrastructure providers.'),
                    ],
                  ),
                  const SizedBox(height: 16),

                  _SectionCard(
                    icon: Icons.account_balance_rounded,
                    title: '5. Financial Terms',
                    color: AppTheme.danger,
                    content: [
                      _Clause('5.1 Premium Payment', 'Policy premiums are collected via Razorpay payment gateway. By purchasing a policy, you authorize the deduction of the stated premium amount.'),
                      _Clause('5.2 UPI Payouts', 'Approved claim payouts are transferred to your registered UPI ID within 24 hours of approval. Susanoo is not liable for delays caused by your bank or UPI provider.'),
                      _Clause('5.3 Dispute Resolution', 'Any disputes regarding claim amounts or rejections must be raised within 30 days of the claim decision. Disputes are resolved through our internal review process, followed by arbitration if unresolved.'),
                      _Clause('5.4 Governing Law', 'These terms are governed by the laws of India. Any legal proceedings shall be subject to the exclusive jurisdiction of courts in Bangalore, Karnataka.'),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // Last updated
                  Center(
                    child: Text(
                      s.lastUpdated,
                      style: TextStyle(fontSize: 11, color: AppTheme.textHint),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Checkboxes
                  _ConsentCheckbox(
                    value: _acceptedTerms,
                    onChanged: (v) => setState(() => _acceptedTerms = v ?? false),
                    text: s.acceptTermsOfService,
                  ),
                  const SizedBox(height: 12),
                  _ConsentCheckbox(
                    value: _acceptedPrivacy,
                    onChanged: (v) => setState(() => _acceptedPrivacy = v ?? false),
                    text: s.acceptPrivacyPolicy,
                  ),
                  const SizedBox(height: 12),
                  _ConsentCheckbox(
                    value: _acceptedDataConsent,
                    onChanged: (v) => setState(() => _acceptedDataConsent = v ?? false),
                    text: s.acceptDataConsent,
                  ),
                  const SizedBox(height: 28),
                ],
              ),
            ),

            // Bottom accept bar
            Container(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
              decoration: BoxDecoration(
                color: Colors.white,
                border: const Border(top: BorderSide(color: AppTheme.divider, width: 0.5)),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 8, offset: const Offset(0, -2)),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (!_hasScrolledToBottom)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.keyboard_arrow_down_rounded, size: 16, color: AppTheme.textHint),
                          const SizedBox(width: 4),
                          Text(s.scrollToRead,
                              style: TextStyle(fontSize: 12, color: AppTheme.textHint)),
                        ],
                      ),
                    ),
                  AnimatedOpacity(
                    opacity: allAccepted ? 1.0 : 0.5,
                    duration: const Duration(milliseconds: 300),
                    child: ElevatedButton(
                      onPressed: allAccepted ? _accept : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primary,
                        minimumSize: const Size(double.infinity, 54),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.check_circle_rounded, size: 20, color: Colors.white),
                          const SizedBox(width: 8),
                          Text(
                            allAccepted ? s.acceptAndContinue : s.acceptAllToContinue,
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.white),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    s.confirmAge,
                    style: TextStyle(fontSize: 11, color: AppTheme.textHint),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Clause {
  final String title;
  final String body;
  const _Clause(this.title, this.body);
}

class _SectionCard extends StatefulWidget {
  final IconData icon;
  final String title;
  final Color color;
  final List<_Clause> content;
  const _SectionCard({required this.icon, required this.title, required this.color, required this.content});

  @override
  State<_SectionCard> createState() => _SectionCardState();
}

class _SectionCardState extends State<_SectionCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.divider, width: 0.5),
      ),
      child: Column(
        children: [
          // Header — always visible, tap to expand
          InkWell(
            onTap: () => setState(() => _expanded = !_expanded),
            borderRadius: BorderRadius.circular(16),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: widget.color.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(widget.icon, color: widget.color, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(widget.title,
                        style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                  ),
                  Icon(
                    _expanded ? Icons.keyboard_arrow_up_rounded : Icons.keyboard_arrow_down_rounded,
                    color: AppTheme.textSecondary,
                  ),
                ],
              ),
            ),
          ),
          // Expandable clauses
          if (_expanded) ...[
            const Divider(height: 1, color: AppTheme.divider),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: widget.content.map((clause) => Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(clause.title,
                          style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: widget.color)),
                      const SizedBox(height: 4),
                      Text(clause.body,
                          style: const TextStyle(
                              fontSize: 13,
                              color: AppTheme.textSecondary,
                              height: 1.6)),
                    ],
                  ),
                )).toList(),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _ConsentCheckbox extends StatelessWidget {
  final bool value;
  final ValueChanged<bool?> onChanged;
  final String text;
  const _ConsentCheckbox({
    required this.value,
    required this.onChanged,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: value ? AppTheme.primaryLight : Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: value ? AppTheme.primary : AppTheme.divider,
          width: value ? 1.5 : 0.5,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 24,
            height: 24,
            child: Checkbox(
              value: value,
              onChanged: onChanged,
              activeColor: AppTheme.primary,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary, height: 1.5),
            ),
          ),
        ],
      ),
    );
  }
}
