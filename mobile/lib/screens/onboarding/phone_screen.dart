import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';
import 'package:susanoo/l10n/app_strings.dart';
import 'package:susanoo/providers/locale_provider.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';

class PhoneScreen extends ConsumerStatefulWidget {
  const PhoneScreen({super.key});

  @override
  ConsumerState<PhoneScreen> createState() => _PhoneScreenState();
}

class _PhoneScreenState extends ConsumerState<PhoneScreen> {
  final _phoneCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  late VideoPlayerController _videoCtrl;

  @override
  void initState() {
    super.initState();
    _videoCtrl = VideoPlayerController.asset('assets/videos/naruto_bg.mp4')
      ..initialize().then((_) {
        _videoCtrl.setLooping(true);
        _videoCtrl.setVolume(0);
        _videoCtrl.play();
        if (mounted) setState(() {});
      });
  }

  @override
  void dispose() {
    _phoneCtrl.dispose();
    _videoCtrl.dispose();
    super.dispose();
  }

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final phone = '+91${_phoneCtrl.text.trim()}';
    try {
      await ref.read(authProvider.notifier).sendOtp(phone);
      if (mounted) context.push('/auth/otp', extra: phone);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Error: $e'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final s = ref.watch(stringsProvider);
    final currentLang = ref.watch(localeProvider);

    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          if (_videoCtrl.value.isInitialized)
            FittedBox(
              fit: BoxFit.cover,
              child: SizedBox(
                width: _videoCtrl.value.size.width,
                height: _videoCtrl.value.size.height,
                child: VideoPlayer(_videoCtrl),
              ),
            ),
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Color(0xAA000000), Color(0xCC000000)],
              ),
            ),
          ),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Language picker pills
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: AppStrings.all.entries.map((entry) {
                        final isSelected = entry.key == currentLang;
                        return GestureDetector(
                          onTap: () => ref
                              .read(localeProvider.notifier)
                              .setLanguage(entry.key),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            margin: const EdgeInsets.only(left: 6),
                            padding: const EdgeInsets.symmetric(
                                horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? Colors.white
                                  : Colors.white.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: isSelected
                                    ? Colors.white
                                    : Colors.white.withOpacity(0.3),
                              ),
                            ),
                            child: Text(
                              entry.value.languageName,
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: isSelected
                                    ? FontWeight.w700
                                    : FontWeight.w400,
                                color: isSelected
                                    ? AppTheme.primary
                                    : Colors.white,
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                    ),

                    const SizedBox(height: 24),
                    Container(
                      width: 64,
                      height: 64,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(16),
                        border:
                            Border.all(color: Colors.white.withOpacity(0.3)),
                      ),
                      child: const Icon(Icons.shield_rounded,
                          color: Colors.white, size: 36),
                    ),
                    const SizedBox(height: 32),
                    Text(
                      s.welcome,
                      style: const TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.w800,
                          height: 1.2,
                          color: Colors.white),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      s.welcomeSub,
                      style: TextStyle(
                          fontSize: 16,
                          color: Colors.white.withOpacity(0.8),
                          height: 1.5),
                    ),
                    const SizedBox(height: 40),

                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(16),
                        border:
                            Border.all(color: Colors.white.withOpacity(0.2)),
                      ),
                      child: Column(
                        children: [
                          Theme(
                            data: Theme.of(context).copyWith(
                              inputDecorationTheme: const InputDecorationTheme(
                                filled: true,
                                fillColor: Colors.transparent,
                              ),
                            ),
                            child: TextFormField(
                              controller: _phoneCtrl,
                              keyboardType: TextInputType.phone,
                              style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600),
                              inputFormatters: [
                                FilteringTextInputFormatter.digitsOnly,
                                LengthLimitingTextInputFormatter(10),
                              ],
                              decoration: InputDecoration(
                                prefixText: '+91  ',
                                prefixStyle: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                    color: Colors.white),
                                hintText: '9876543210',
                                hintStyle: TextStyle(
                                    color: Colors.white.withOpacity(0.4)),
                                labelText: s.mobileNumber,
                                labelStyle: TextStyle(
                                    color: Colors.white.withOpacity(0.7)),
                                filled: true,
                                fillColor: Colors.white.withOpacity(0.08),
                                enabledBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(10),
                                  borderSide: BorderSide(
                                      color: Colors.white.withOpacity(0.3)),
                                ),
                                focusedBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(10),
                                  borderSide:
                                      const BorderSide(color: Colors.white),
                                ),
                                errorBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(10),
                                  borderSide:
                                      BorderSide(color: AppTheme.danger),
                                ),
                                focusedErrorBorder: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(10),
                                  borderSide:
                                      BorderSide(color: AppTheme.danger),
                                ),
                              ),
                              validator: (v) {
                                if (v == null || v.length != 10)
                                  return s.invalidPhone;
                                return null;
                              },
                            ),
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton(
                            onPressed: auth.isLoading ? null : _submit,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.primary,
                              minimumSize: const Size(double.infinity, 52),
                            ),
                            child: auth.isLoading
                                ? Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      const SizedBox(
                                          height: 20,
                                          width: 20,
                                          child: CircularProgressIndicator(
                                              color: Colors.white,
                                              strokeWidth: 2)),
                                      const SizedBox(width: 12),
                                      Text(s.sendingOtp,
                                          style: const TextStyle(
                                              color: Colors.white)),
                                    ],
                                  )
                                : Text(s.sendOtp),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.4),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                            color: const Color(0xFFFFE082).withOpacity(0.5)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.info_outline_rounded,
                                  size: 16, color: Color(0xFFF59E0B)),
                              const SizedBox(width: 6),
                              Text(s.howItWorks,
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                      fontSize: 13,
                                      color: Color(0xFFFFE082))),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(s.howItWorksReal,
                              style: const TextStyle(
                                  fontSize: 12,
                                  color: Colors.white70,
                                  height: 1.5)),
                          Text(s.howItWorksDemo,
                              style: const TextStyle(
                                  fontSize: 12,
                                  color: Colors.white70,
                                  height: 1.5)),
                        ],
                      ),
                    ),

                    if (auth.isLoading)
                      Padding(
                        padding: const EdgeInsets.only(top: 12),
                        child: Center(
                          child: Text(
                            s.serverWakeup,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                                fontSize: 12, color: Colors.white54),
                          ),
                        ),
                      ),
                    const SizedBox(height: 16),
                    Center(
                      child: Text(
                        s.termsPrivacy,
                        style: TextStyle(
                            fontSize: 12, color: Colors.white.withOpacity(0.4)),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
