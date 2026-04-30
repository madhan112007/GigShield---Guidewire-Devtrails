import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:susanoo/utils/constants.dart';

class ApiService {
  late final Dio _dio;
  final _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(
        accessibility: KeychainAccessibility.first_unlock_this_device),
  );

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 60),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: AppConstants.accessTokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) async {
        if (e.response?.statusCode == 401) {
          // Attempt silent token refresh before giving up
          final refreshed = await _tryRefresh();
          if (refreshed) {
            // Retry the original request with the new token
            final token = await _storage.read(key: AppConstants.accessTokenKey);
            final opts = e.requestOptions;
            opts.headers['Authorization'] = 'Bearer $token';
            try {
              final response = await _dio.fetch(opts);
              return handler.resolve(response);
            } catch (_) {}
          }
          // Refresh failed — clear storage so app redirects to login
          await _storage.deleteAll();
          return handler.next(DioException(
            requestOptions: e.requestOptions,
            response: e.response,
            type: DioExceptionType.badResponse,
            error: 'Session expired. Please login again.',
          ));
        }
        return handler.next(e);
      },
    ));
  }

  Future<bool> _tryRefresh() async {
    final refreshToken = await _storage.read(key: AppConstants.refreshTokenKey);
    if (refreshToken == null) return false;
    try {
      // Use a plain Dio instance (no interceptors) to avoid infinite loop
      final res = await Dio(BaseOptions(baseUrl: AppConstants.baseUrl)).post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final newAccess = res.data['access_token'] as String?;
      if (newAccess == null) return false;
      await _storage.write(key: AppConstants.accessTokenKey, value: newAccess);
      await _storage.write(
          key: AppConstants.devModeKey,
          value: '${res.data['is_dev_mode'] == true}');
      return true;
    } catch (_) {
      return false;
    }
  }

  // ── Auth ──────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> sendOtp(String phone) async {
    final res = await _dio.post('/auth/send-otp',
        data: {'phone': phone},
        options: Options(
            sendTimeout: const Duration(seconds: 60),
            receiveTimeout: const Duration(seconds: 60)));
    return res.data;
  }

  Future<Map<String, dynamic>> verifyOtp(String phone, String otp) async {
    final res =
        await _dio.post('/auth/verify-otp', data: {'phone': phone, 'otp': otp});
    return res.data;
  }

  Future<void> saveTokens(String access, String refresh, String workerId,
      {bool isDevMode = false}) async {
    await _storage.write(key: AppConstants.accessTokenKey, value: access);
    await _storage.write(key: AppConstants.refreshTokenKey, value: refresh);
    await _storage.write(key: AppConstants.workerIdKey, value: workerId);
    await _storage.write(key: AppConstants.devModeKey, value: '$isDevMode');
  }

  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: AppConstants.accessTokenKey);
    return token != null;
  }

  Future<bool> isDevMode() async {
    final value = await _storage.read(key: AppConstants.devModeKey);
    return value == 'true';
  }

  Future<void> logout() async {
    await _storage.deleteAll();
  }

  // ── Worker ────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> registerWorker(Map<String, dynamic> data) async {
    final res = await _dio.post('/workers/register', data: data);
    return res.data;
  }

  Future<Map<String, dynamic>> getMe() async {
    final res = await _dio.get('/workers/me');
    return res.data;
  }

  Future<Map<String, dynamic>> getPlatformEarnings(String platform) async {
    final res = await _dio.get('/workers/platform-earnings',
        queryParameters: {'platform': platform});
    return res.data;
  }

  Future<Map<String, dynamic>> getDashboard() async {
    final res = await _dio.get('/workers/dashboard');
    return res.data;
  }

  // ── Policies ──────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getPremiumQuote(String tier) async {
    final res =
        await _dio.get('/policies/quote', queryParameters: {'tier': tier});
    return res.data;
  }

  Future<Map<String, dynamic>> createPolicyOrder(String tier) async {
    final res = await _dio.post('/policies/create-order', data: {'tier': tier});
    return res.data;
  }

  Future<Map<String, dynamic>> verifyPolicyPayment(
      Map<String, dynamic> data) async {
    final res = await _dio.post('/policies/verify-payment', data: data);
    return res.data;
  }

  Future<Map<String, dynamic>> createPolicy(String tier) async {
    final res = await _dio.post('/policies/', data: {'tier': tier});
    return res.data;
  }

  Future<Map<String, dynamic>> getActivePolicy() async {
    final res = await _dio.get('/policies/active');
    return res.data;
  }

  Future<List<dynamic>> listPolicies() async {
    final res = await _dio.get('/policies/');
    return res.data;
  }

  // ── Disruptions ───────────────────────────────────────────────────────────

  Future<List<dynamic>> getActiveDisruptions(String city) async {
    final res =
        await _dio.get('/disruptions/active', queryParameters: {'city': city});
    return res.data;
  }

  Future<List<dynamic>> simulateDisruption(String city, String pincode) async {
    final res = await _dio.post(
      '/disruptions/simulate',
      queryParameters: {'city': city, 'pincode': pincode},
    );
    return res.data;
  }

  // ── Claims ────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> triggerClaim(String disruptionEventId) async {
    final res = await _dio.post('/claims/trigger/$disruptionEventId');
    return res.data;
  }

  Future<List<dynamic>> listClaims() async {
    final res = await _dio.get('/claims/');
    return res.data;
  }

  // ── Payouts ───────────────────────────────────────────────────────────────

  Future<List<dynamic>> listPayouts() async {
    final res = await _dio.get('/payouts/');
    return res.data;
  }

  Future<Map<String, dynamic>> sendLocationPing(
      double lat, double lng, double accuracy) async {
    final res = await _dio.post('/location/ping', data: {
      'lat': lat,
      'lng': lng,
      'accuracy': accuracy,
    });
    return res.data;
  }

  Future<Map<String, dynamic>> getRiskAssessment() async {
    final res = await _dio.get('/workers/dashboard');
    return res.data;
  }

  Future<Map<String, dynamic>> getWeatherByLocation(
      double lat, double lon) async {
    final res = await _dio
        .get('/location/weather', queryParameters: {'lat': lat, 'lon': lon});
    return res.data;
  }

  Future<void> registerFcmToken(String token) async {
    await _dio.post('/workers/fcm-token', data: {'fcm_token': token});
  }

  // ── Notifications ─────────────────────────────────────────────────────────

  Future<List<dynamic>> listNotifications() async {
    final res = await _dio.get('/notifications');
    return res.data;
  }

  Future<void> markNotificationRead(String id) async {
    await _dio.post('/notifications/$id/read');
  }

  Future<void> markAllNotificationsRead() async {
    await _dio.post('/notifications/read-all');
  }
}
