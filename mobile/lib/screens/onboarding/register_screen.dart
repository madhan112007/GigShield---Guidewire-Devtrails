import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/utils/constants.dart';
import 'package:susanoo/services/city_service.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _nameCtrl = TextEditingController();
  final _upiCtrl = TextEditingController();
  final _pincodeCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  String? _selectedCity;
  String _selectedPincode = '';
  bool _loading = false;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _upiCtrl.dispose();
    _pincodeCtrl.dispose();
    super.dispose();
  }

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);

    final platform = ref.read(authProvider).selectedPlatform ?? 'blinkit';

    try {
      await ref.read(apiServiceProvider).registerWorker({
        'name': _nameCtrl.text.trim(),
        'platform': platform,
        'city': _selectedCity ?? 'Bangalore',
        'pincode': _pincodeCtrl.text.trim(),
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

                // City autocomplete — GeoDB API with bundled fallback
                const Text('Your City',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 8),
                Autocomplete<CityResult>(
                  displayStringForOption: (r) => r.city,
                  optionsBuilder: (TextEditingValue v) async {
                    if (v.text.trim().length < 2) return [];
                    return CityService.search(v.text.trim());
                  },
                  onSelected: (result) => setState(() {
                    _selectedCity = result.city;
                    _selectedPincode = result.pincode;
                  }),
                  fieldViewBuilder: (context, ctrl, focusNode, onSubmit) {
                    if (_selectedCity != null && ctrl.text.isEmpty) {
                      ctrl.text = _selectedCity!;
                    }
                    return TextFormField(
                      controller: ctrl,
                      focusNode: focusNode,
                      decoration: InputDecoration(
                        hintText: 'Type city name e.g. Coimbatore',
                        suffixIcon: _selectedCity != null
                            ? const Icon(Icons.check_circle_rounded,
                                color: AppTheme.success, size: 20)
                            : const Icon(Icons.search_rounded,
                                color: AppTheme.textHint, size: 20),
                      ),
                      validator: (_) =>
                          _selectedCity == null ? 'Please select a city' : null,
                      onChanged: (_) {
                        if (_selectedCity != null) {
                          setState(() {
                            _selectedCity = null;
                            _selectedPincode = '';
                          });
                        }
                      },
                    );
                  },
                  optionsViewBuilder: (context, onSelected, options) => Align(
                    alignment: Alignment.topLeft,
                    child: Material(
                      elevation: 4,
                      borderRadius: BorderRadius.circular(12),
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 340),
                        child: ListView(
                          padding: EdgeInsets.zero,
                          shrinkWrap: true,
                          children: options.map((r) => ListTile(
                            dense: true,
                            leading: const Icon(Icons.location_on_rounded,
                                color: AppTheme.primary, size: 18),
                            title: Text(r.city,
                                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                            subtitle: Text(r.state,
                                style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                            onTap: () => onSelected(r),
                          )).toList(),
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Pincode — ward-level, used for AI-powered premium pricing
                const Text('Your Delivery Area Pincode',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryLight,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.info_outline_rounded, size: 14, color: AppTheme.primary),
                      SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Enter the pincode of the area where you deliver — not your home pincode. This sets your ward-level premium.',
                          style: TextStyle(fontSize: 11, color: AppTheme.primary, height: 1.4),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _pincodeCtrl,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  decoration: const InputDecoration(
                    hintText: 'e.g. 641035 (your delivery zone)',
                    counterText: '',
                    suffixIcon: Icon(Icons.pin_drop_rounded,
                        color: AppTheme.textHint, size: 20),
                  ),
                  validator: (v) {
                    final val = v?.trim() ?? '';
                    if (val.isEmpty) return 'Enter your delivery area pincode';
                    if (val.length != 6) return 'Pincode must be 6 digits';
                    if (!RegExp(r'^[1-9][0-9]{5}$').hasMatch(val)) return 'Enter a valid Indian pincode';
                    return null;
                  },
                ),

                const SizedBox(height: 20),
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
