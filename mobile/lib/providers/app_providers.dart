import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:susanoo/services/api_service.dart';
import 'package:susanoo/services/firebase_service.dart';
import 'package:susanoo/services/location_service.dart';

// ── Core providers ────────────────────────────────────────────────────────────

final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

// ── Auth state ────────────────────────────────────────────────────────────────

class AuthState {
  final bool isLoggedIn;
  final bool isNewUser;
  final String? workerId;
  final String? selectedPlatform;
  final bool isLoading;
  final String? error;
  const AuthState({
    this.isLoggedIn = false,
    this.isNewUser = false,
    this.workerId,
    this.selectedPlatform,
    this.isLoading = false,
    this.error,
  });
  AuthState copyWith({bool? isLoggedIn, bool? isNewUser, String? workerId, String? selectedPlatform, bool? isLoading, String? error}) =>
      AuthState(
        isLoggedIn: isLoggedIn ?? this.isLoggedIn,
        isNewUser: isNewUser ?? this.isNewUser,
        workerId: workerId ?? this.workerId,
        selectedPlatform: selectedPlatform ?? this.selectedPlatform,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiService _api;
  AuthNotifier(this._api) : super(const AuthState()) {
    _checkAuth();
  }

  Future<void> _registerFcmToken() async {
    try {
      final token = await FirebaseService.getToken();
      if (token != null) await _api.registerFcmToken(token);
    } catch (_) {}
  }

  Future<void> _checkAuth() async {
    final loggedIn = await _api.isLoggedIn();
    state = state.copyWith(isLoggedIn: loggedIn);
    if (loggedIn) {
      LocationService.startTracking(_api);
      await _registerFcmToken();
    }
  }

  Future<void> forceLogout() async {
    await _api.logout();
    state = const AuthState();
  }

  Future<Map<String, dynamic>> sendOtp(String phone) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final res = await _api.sendOtp(phone);
      state = state.copyWith(isLoading: false);
      return res;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      rethrow;
    }
  }

  Future<bool> verifyOtp(String phone, String otp) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final res = await _api.verifyOtp(phone, otp);
      await _api.saveTokens(
        res['access_token'],
        res['refresh_token'],
        res['worker_id'],
      );
      final isNew = res['is_new_user'] ?? false;
      state = state.copyWith(
        isLoggedIn: !isNew,
        isNewUser: isNew,
        workerId: res['worker_id'],
        isLoading: false,
      );
      if (!isNew) await _registerFcmToken();
      return isNew;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Invalid OTP. Try again.');
      return false;
    }
  }

  Future<void> completeRegistration() async {
    state = state.copyWith(isLoggedIn: true, isNewUser: false);
    LocationService.startTracking(_api);
    await _registerFcmToken();
  }

  void setPlatform(String platform) {
    state = state.copyWith(selectedPlatform: platform);
  }

  Future<void> logout() async {
    await _api.logout();
    state = const AuthState(isNewUser: false);
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(ref.watch(apiServiceProvider)),
);

// ── Worker/Dashboard state ─────────────────────────────────────────────────────

final dashboardProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  try {
    return await api.getDashboard();
  } on Exception catch (e) {
    if (e.toString().contains('401') || e.toString().contains('deleteAll')) {
      ref.read(authProvider.notifier).forceLogout();
    }
    rethrow;
  }
});

final activePolicyProvider = FutureProvider.autoDispose<Map<String, dynamic>?>((ref) async {
  final api = ref.watch(apiServiceProvider);
  try {
    return await api.getActivePolicy();
  } catch (_) {
    return null;
  }
});

final activeDisruptionsProvider = FutureProvider.autoDispose.family<List<dynamic>, String>(
  (ref, city) async {
    final api = ref.watch(apiServiceProvider);
    return api.getActiveDisruptions(city);
  },
);

final claimsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.listClaims();
});

final notificationsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.listNotifications();
});

final payoutsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.listPayouts();
});

// ── Premium Quote ─────────────────────────────────────────────────────────────

final premiumQuoteProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, String>(
  (ref, tier) async {
    final api = ref.watch(apiServiceProvider);
    return api.getPremiumQuote(tier);
  },
);

// ── Dev mode (unlocked by using OTP 123456) ──────────────────────────────────
final devModeProvider = StateProvider<bool>((ref) => false);

// ── Selected tier for policy purchase ─────────────────────────────────────────

final selectedTierProvider = StateProvider<String>((ref) => 'smart');

// ── Live Risk Assessment ───────────────────────────────────────────────────────

final liveRiskProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  try {
    return await api.getRiskAssessment();
  } on Exception catch (e) {
    if (e.toString().contains('401') || e.toString().contains('deleteAll')) {
      ref.read(authProvider.notifier).forceLogout();
    }
    rethrow;
  }
});

// ── Live Weather by GPS ────────────────────────────────────────────────────────

final liveWeatherProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);

  double? lat, lon;

  // Prefer worker's last known location stored by the backend
  final riskData = ref.watch(liveRiskProvider).valueOrNull;
  if (riskData != null) {
    final worker = riskData['worker'] as Map<String, dynamic>? ?? {};
    lat = (worker['last_known_lat'] as num?)?.toDouble();
    lon = (worker['last_known_lng'] as num?)?.toDouble();
  }

  // Fall back to live GPS if no stored location yet
  if (lat == null || lon == null) {
    final pos = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.medium,
      timeLimit: const Duration(seconds: 8),
    );
    lat = pos.latitude;
    lon = pos.longitude;
  }

  return api.getWeatherByLocation(lat!, lon!);
});
