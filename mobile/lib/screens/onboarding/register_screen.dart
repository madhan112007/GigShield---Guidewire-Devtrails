import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/utils/constants.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _nameCtrl = TextEditingController();
  final _upiCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  String? _selectedCity;
  String _pincode = '560001';
  bool _loading = false;

  final Map<String, String> _cityPincode = {
    'Bangalore': '560001',
    'Mumbai': '400001',
    'Delhi': '110001',
    'Chennai': '600001',
    'Hyderabad': '500001',
    'Pune': '411001',
    'Kolkata': '700001',
  };

  @override
  void dispose() {
    _nameCtrl.dispose();
    _upiCtrl.dispose();
    super.dispose();
  }

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);

    final platform = ref.read(authProvider).selectedPlatform ?? 'blinkit';

    try {
      await ref.read(apiServiceProvider).registerWorker({
        'phone': '',
        'name': _nameCtrl.text.trim(),
        'platform': platform,
        'city': _selectedCity ?? 'Bangalore',
        'pincode': _pincode,
        'upi_id': _upiCtrl.text.trim().isEmpty ? null : _upiCtrl.text.trim(),
      });
      await ref.read(authProvider.notifier).completeRegistration();
      if (mounted) context.go('/home');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Error: $e'), backgroundColor: AppTheme.danger),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final platform = ref.watch(authProvider).selectedPlatform ?? 'blinkit';
    final platformLabel = AppConstants.platforms.firstWhere(
        (p) => p['value'] == platform,
        orElse: () => {'label': platform})['label']!;

    return Scaffold(
      appBar: AppBar(title: const Text('Almost there!')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Just a few more details',
                    style:
                        TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
                const SizedBox(height: 6),
                const Text(
                    'Your earnings are already fetched. We just need your name.',
                    style:
                        TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
                const SizedBox(height: 24),

                // Platform badge (read-only)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryLight,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.verified_rounded,
                          color: AppTheme.primary, size: 16),
                      const SizedBox(width: 8),
                      Text('Platform: $platformLabel',
                          style: const TextStyle(
                              color: AppTheme.primary,
                              fontWeight: FontWeight.w700,
                              fontSize: 13)),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Name
                const Text('Full Name',
                    style:
                        TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _nameCtrl,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(hintText: 'Ravi Kumar'),
                  validator: (v) =>
                      v == null || v.trim().isEmpty ? 'Enter your name' : null,
                ),
                const SizedBox(height: 20),

                // City
                const Text('Your City',
                    style:
                        TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: _selectedCity,
                  decoration:
                      const InputDecoration(hintText: 'Select your city'),
                  items: AppConstants.supportedCities
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  validator: (v) =>
                      v == null ? 'Please select your city' : null,
                  onChanged: (v) => setState(() {
                    _selectedCity = v!;
                    _pincode = _cityPincode[v] ?? '560001';
                  }),
                ),
                const SizedBox(height: 20),

                // UPI (optional)
                const Text('UPI ID (for instant payouts)',
                    style:
                        TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _upiCtrl,
                  decoration: const InputDecoration(
                    hintText: 'ravi@upi (optional)',
                    suffixIcon: Icon(Icons.account_balance_wallet_outlined),
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  '💡 Claims are credited to your UPI within minutes of a disruption.',
                  style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                ),

                const SizedBox(height: 40),
                ElevatedButton(
                  onPressed: _loading ? null : _submit,
                  child: _loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2))
                      : const Text('Start Protection →'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
