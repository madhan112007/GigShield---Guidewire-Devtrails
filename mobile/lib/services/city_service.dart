import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/services.dart';

class CityResult {
  final String city;
  final String state;
  final String pincode;
  CityResult({required this.city, required this.state, required this.pincode});
}

class CityService {
  static const _apiKey = 'REMOVED_API_KEY';

  static final _dio = Dio(BaseOptions(
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 5),
  ));

  // Bundled fallback — loaded once and cached
  static List<CityResult>? _fallback;

  static Future<List<CityResult>> _loadFallback() async {
    if (_fallback != null) return _fallback!;
    final raw = await rootBundle.loadString('assets/data/indian_cities.json');
    final list = jsonDecode(raw) as List;
    _fallback = list
        .map((e) => CityResult(
              city: e['city'] as String,
              state: e['state'] as String,
              pincode: e['pincode'] as String,
            ))
        .toList();
    return _fallback!;
  }

  /// Search cities — tries Positionstack first, falls back to bundled JSON
  static Future<List<CityResult>> search(String query) async {
    if (query.trim().length < 2) return [];
    try {
      final results = await _searchPositionstack(query);
      if (results.isNotEmpty) return results;
      return _searchFallback(query);
    } catch (_) {
      return _searchFallback(query);
    }
  }

  static Future<List<CityResult>> _searchPositionstack(String query) async {
    final res = await _dio.get(
      'http://api.positionstack.com/v1/forward',
      queryParameters: {
        'access_key': _apiKey,
        'query': '$query, India',
        'country': 'IN',
        'limit': 8,
        'output': 'json',
      },
    );

    final data = res.data['data'] as List? ?? [];
    final seen = <String>{};
    final results = <CityResult>[];

    for (final e in data) {
      final city = (e['locality'] as String? ??
              e['county'] as String? ??
              e['region'] as String? ??
              '')
          .trim();
      final state = (e['region'] as String? ?? '').trim();
      final postal = (e['postal_code'] as String? ?? '').trim();

      if (city.isEmpty || seen.contains(city)) continue;
      seen.add(city);
      results.add(CityResult(city: city, state: state, pincode: postal));
    }
    return results;
  }

  static Future<List<CityResult>> _searchFallback(String query) async {
    final cities = await _loadFallback();
    final q = query.toLowerCase();
    return cities.where((c) => c.city.toLowerCase().contains(q)).take(8).toList();
  }
}
