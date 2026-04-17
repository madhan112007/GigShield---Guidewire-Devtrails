import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:susanoo/providers/locale_provider.dart';
import 'package:susanoo/router/app_router.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/services/firebase_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FirebaseService.initialize();
  FirebaseService.setupForegroundHandler();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );
  runApp(const ProviderScope(child: SusanooApp()));
}

class SusanooApp extends ConsumerWidget {
  const SusanooApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    final locale = ref.watch(localeMaterialProvider);
    return MaterialApp.router(
      title: 'Susanoo',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      locale: locale,
      routerConfig: router,
      builder: (context, child) => _LocationPermissionWrapper(child: child!),
    );
  }
}

class _LocationPermissionWrapper extends ConsumerStatefulWidget {
  final Widget child;
  const _LocationPermissionWrapper({required this.child});

  @override
  ConsumerState<_LocationPermissionWrapper> createState() =>
      _LocationPermissionWrapperState();
}

class _LocationPermissionWrapperState
    extends ConsumerState<_LocationPermissionWrapper> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkPermission());
  }

  Future<void> _checkPermission() async {
    final permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.always ||
        permission == LocationPermission.whileInUse) return;

    if (permission == LocationPermission.deniedForever) {
      await Future.delayed(const Duration(milliseconds: 800));
      if (mounted) _showSettingsDialog();
      return;
    }

    // First launch or previously denied — request directly to trigger native OS dialog
    final result = await Geolocator.requestPermission();
    if ((result == LocationPermission.denied) && mounted) {
      // User denied — show our rationale dialog for next time
      await Future.delayed(const Duration(milliseconds: 400));
      if (mounted) _showPermissionDialog();
    }
  }

  void _showSettingsDialog() {
    final s = ref.read(stringsProvider);
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        contentPadding: const EdgeInsets.all(24),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.location_off_rounded, color: AppTheme.warning, size: 48),
            const SizedBox(height: 16),
            Text(s.locationNeeded,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                textAlign: TextAlign.center),
            const SizedBox(height: 12),
            Text(s.locationNeededDesc,
                style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary, height: 1.5),
                textAlign: TextAlign.center),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () { Navigator.pop(context); openAppSettings(); },
                child: Text(s.openSettings),
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(s.notNow, style: const TextStyle(color: AppTheme.textSecondary)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showPermissionDialog() {
    final s = ref.read(stringsProvider);
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        contentPadding: const EdgeInsets.all(24),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: const BoxDecoration(color: AppTheme.primaryLight, shape: BoxShape.circle),
              child: const Icon(Icons.location_on_rounded, color: AppTheme.primary, size: 36),
            ),
            const SizedBox(height: 20),
            Text(s.allowLocation,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                textAlign: TextAlign.center),
            const SizedBox(height: 12),
            Text(s.allowLocationDesc,
                style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary, height: 1.5),
                textAlign: TextAlign.center),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF8E1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFFFFE082)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline_rounded, size: 14, color: Color(0xFFF59E0B)),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(s.changeAnytime,
                        style: const TextStyle(fontSize: 11, color: Color(0xFF78350F))),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () async {
                  Navigator.pop(context);
                  final result = await Geolocator.requestPermission();
                  if ((result == LocationPermission.denied ||
                          result == LocationPermission.deniedForever) &&
                      mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(s.allowLocationDesc),
                        action: SnackBarAction(label: s.openSettings, onPressed: openAppSettings),
                      ),
                    );
                  }
                },
                child: Text(s.allowLocationBtn),
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(s.notNow, style: const TextStyle(color: AppTheme.textSecondary)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
