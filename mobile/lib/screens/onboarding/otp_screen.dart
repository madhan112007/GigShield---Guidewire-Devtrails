import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:pinput/pinput.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/services/firebase_service.dart';
import 'dart:async';

class OtpScreen extends ConsumerStatefulWidget {
  final String phone;
  const OtpScreen({super.key, required this.phone});

  @override
  ConsumerState<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends ConsumerState<OtpScreen> {
  final _otpCtrl = TextEditingController();
  int _resendSeconds = 30;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (_resendSeconds == 0) {
        t.cancel();
      } else {
        setState(() => _resendSeconds--);
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _otpCtrl.dispose();
    super.dispose();
  }

  void _verify(String otp) async {
    if (otp.length != 6) return;
    // Set dev mode if using 123456
    if (otp == '123456') {
      ref.read(devModeProvider.notifier).state = true;
    }
    final isNew = await ref.read(authProvider.notifier).verifyOtp(widget.phone, otp);
    if (!mounted) return;
    if (ref.read(authProvider).error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(ref.read(authProvider).error!), backgroundColor: AppTheme.danger),
      );
      return;
    }
    // Register FCM token after successful login
    _registerFcmToken();
    context.go(isNew ? '/auth/register' : '/home');
  }

  void _registerFcmToken() async {
    final token = await FirebaseService.getToken();
    if (token != null) {
      try {
        await ref.read(apiServiceProvider).post('/workers/fcm-token', {'fcm_token': token});
        print('[FCM] Token registered: ${token.substring(0, 20)}...');
      } catch (e) {
        print('[FCM] Token registration failed: $e');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final defaultPinTheme = PinTheme(
      width: 56,
      height: 60,
      textStyle: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.divider),
        borderRadius: BorderRadius.circular(12),
      ),
    );

    return Scaffold(
      appBar: AppBar(leading: BackButton(onPressed: () => context.pop())),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 24),
              const Text('Enter OTP', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              RichText(
                text: TextSpan(
                  style: const TextStyle(fontSize: 16, color: AppTheme.textSecondary),
                  children: [
                    const TextSpan(text: 'We sent a 6-digit code to\n'),
                    TextSpan(
                      text: widget.phone,
                      style: const TextStyle(fontWeight: FontWeight.w700, color: AppTheme.textPrimary),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.primaryLight,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.call_rounded, size: 18, color: AppTheme.primary),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'You may receive a call from +91 8031492487 with your OTP. Do not share it with anyone.',
                        style: TextStyle(fontSize: 12, color: AppTheme.primary, height: 1.5),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
              Pinput(
                controller: _otpCtrl,
                length: 6,
                defaultPinTheme: defaultPinTheme,
                focusedPinTheme: defaultPinTheme.copyDecorationWith(
                  border: Border.all(color: AppTheme.primary, width: 2),
                ),
                onCompleted: _verify,
                autofocus: true,
              ),
              const SizedBox(height: 24),
              if (auth.isLoading)
                const Center(child: CircularProgressIndicator()),
              const SizedBox(height: 16),
              Center(
                child: _resendSeconds > 0
                    ? Text(
                        'Resend OTP in $_resendSeconds s',
                        style: const TextStyle(color: AppTheme.textSecondary),
                      )
                    : TextButton(
                        onPressed: () {
                          setState(() => _resendSeconds = 30);
                          _startTimer();
                          ref.read(authProvider.notifier).sendOtp(widget.phone);
                        },
                        child: const Text('Resend OTP'),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
