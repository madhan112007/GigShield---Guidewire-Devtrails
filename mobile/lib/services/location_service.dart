import 'dart:async';
import 'package:geolocator/geolocator.dart';
import 'package:susanoo/services/api_service.dart';

class LocationService {
  static Timer? _timer;
  static bool _isTracking = false;

  /// Start pinging location every 10 minutes during active hours (6am-10pm)
  static void startTracking(ApiService api) {
    if (_isTracking) return;
    _isTracking = true;
    // Ping immediately on start
    _ping(api);
    // Then every 10 minutes
    _timer = Timer.periodic(const Duration(minutes: 10), (_) => _ping(api));
  }

  static void stopTracking() {
    _timer?.cancel();
    _timer = null;
    _isTracking = false;
  }

  static bool _isActiveHours() {
    final hour = DateTime.now().hour;
    return hour >= 6 && hour < 22; // 6am to 10pm
  }

  static Future<void> _ping(ApiService api) async {
    if (!_isActiveHours()) return;
    try {
      final permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) return;

      final pos = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.low, // network/WiFi only — no GPS chip
        timeLimit: const Duration(seconds: 15),
      );
      await api.sendLocationPing(pos.latitude, pos.longitude, pos.accuracy);
    } catch (_) {
      // Silent fail — location tracking is best-effort
    }
  }
}
